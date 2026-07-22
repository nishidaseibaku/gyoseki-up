/**
 * マスタ配信システム (master-manager) から社員マスタ・部門マスタを取得し、
 * Firestore の names / departments コレクションを置き換える Cloud Function。
 *
 * SPA からは APIキーを扱えない（サーバー側保管が必須）ため、
 * 「設定画面の同期ボタン → syncRequests にドキュメント作成」をトリガに
 * このサーバー側関数が起動してマスタを同期する。
 */
const { onDocumentCreated } = require('firebase-functions/v2/firestore');
const { setGlobalOptions } = require('firebase-functions/v2');
const { defineSecret } = require('firebase-functions/params');
const admin = require('firebase-admin');

admin.initializeApp();
const db = admin.firestore();

// マスタ配信システムの APIキー（Secret Manager 管理。ブラウザには出さない）
const MASTER_API_KEY = defineSecret('MASTER_API_KEY');

const MASTER_API_BASE = 'https://api-yl3qzynteq-an.a.run.app/v1';
// Cloud Run サービスに対する Google ID トークンの audience
const MASTER_API_AUDIENCE = 'https://api-yl3qzynteq-an.a.run.app';

setGlobalOptions({ region: 'asia-northeast1' });

/** メタデータサーバーからサービスアカウントの ID トークンを取得 */
async function getIdToken(audience) {
  const url =
    'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity' +
    `?audience=${encodeURIComponent(audience)}`;
  const res = await fetch(url, { headers: { 'Metadata-Flavor': 'Google' } });
  if (!res.ok) {
    throw new Error(`メタデータからのIDトークン取得に失敗しました: HTTP ${res.status}`);
  }
  return (await res.text()).trim();
}

/** 指定マスタの全 items を取得（cursor ページネーション対応） */
async function fetchMasterItems(masterId, apiKey, idToken) {
  const items = [];
  let cursor = '';
  do {
    const u = new URL(`${MASTER_API_BASE}/masters/${masterId}/items`);
    u.searchParams.set('limit', '1000');
    if (cursor) u.searchParams.set('cursor', cursor);
    const res = await fetch(u, {
      headers: { Authorization: `Bearer ${idToken}`, 'X-API-Key': apiKey },
    });
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`マスタ ${masterId} の取得に失敗しました: HTTP ${res.status} ${body}`);
    }
    const json = await res.json();
    items.push(...(json.data || []));
    cursor = json.meta && json.meta.nextCursor ? json.meta.nextCursor : '';
  } while (cursor);
  return items;
}

/** コレクションを全削除してから name の配列で作り直す */
/** コレクションを全削除してから docs（プレーンオブジェクトの配列）で作り直す */
async function replaceCollection(collectionName, docs) {
  const existing = await db.collection(collectionName).get();
  let batch = db.batch();
  let ops = 0;
  const flush = async () => {
    if (ops > 0) {
      await batch.commit();
      batch = db.batch();
      ops = 0;
    }
  };
  for (const docSnap of existing.docs) {
    batch.delete(docSnap.ref);
    if (++ops >= 450) await flush();
  }
  await flush();
  for (const data of docs) {
    batch.set(db.collection(collectionName).doc(), data);
    if (++ops >= 450) await flush();
  }
  await flush();
}

exports.onMasterSyncRequested = onDocumentCreated(
  { document: 'syncRequests/{reqId}', secrets: [MASTER_API_KEY] },
  async (event) => {
    const snap = event.data;
    if (!snap) return;
    const ref = snap.ref;
    try {
      await ref.update({
        status: 'running',
        startedAt: admin.firestore.FieldValue.serverTimestamp(),
      });

      const idToken = await getIdToken(MASTER_API_AUDIENCE);
      const apiKey = MASTER_API_KEY.value();

      const [employees, departments] = await Promise.all([
        fetchMasterItems('employees', apiKey, idToken),
        fetchMasterItems('departments', apiKey, idToken),
      ]);

      // 部門コード -> 部門名 の対応表（社員の deptCode 解決に使う）
      const deptCodeToName = {};
      departments.forEach((d) => {
        const v = d.values || {};
        if (v.code) deptCodeToName[String(v.code)] = (v.name || '').trim();
      });

      // 社員: 氏名・メール・UPN・部門名を保存（ログインユーザーの照合に使う）
      const seenName = new Set();
      const employeeDocs = [];
      employees
        .filter((e) => e.visible !== false)
        .filter((e) => (e.values?.status ?? 'active') === 'active')
        .forEach((e) => {
          const v = e.values || {};
          const name = (v.displayName || '').trim();
          if (!name || seenName.has(name)) return;
          seenName.add(name);
          employeeDocs.push({
            name,
            email: (v.email || v.userPrincipalName || '').trim().toLowerCase(),
            upn: (v.userPrincipalName || '').trim().toLowerCase(),
            department: v.deptCode ? deptCodeToName[String(v.deptCode)] || '' : '',
          });
        });
      employeeDocs.sort((a, b) => a.name.localeCompare(b.name, 'ja'));

      const seenDept = new Set();
      const departmentDocs = [];
      departments
        .filter((d) => d.visible !== false)
        .forEach((d) => {
          const name = (d.values?.name || '').trim();
          if (name && !seenDept.has(name)) {
            seenDept.add(name);
            departmentDocs.push({ name });
          }
        });
      departmentDocs.sort((a, b) => a.name.localeCompare(b.name, 'ja'));

      await replaceCollection('names', employeeDocs);
      await replaceCollection('departments', departmentDocs);

      await ref.update({
        status: 'done',
        names: employeeDocs.length,
        departments: departmentDocs.length,
        finishedAt: admin.firestore.FieldValue.serverTimestamp(),
      });
    } catch (err) {
      console.error('master sync failed:', err);
      await ref.update({
        status: 'error',
        error: String((err && err.message) || err),
        finishedAt: admin.firestore.FieldValue.serverTimestamp(),
      });
    }
  }
);
