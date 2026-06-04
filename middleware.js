// Vercel Edge Middleware（フレームワーク非依存）
// サイト全体にBASIC認証をかける簡易ガード。
// ※ 認証情報を直書きしています。GitHubがPrivateであることが前提です。
//    将来的には Vercel の環境変数（process.env）へ移すことを推奨します。

export const config = {
  // 全パスを対象（静的アセット含む）
  matcher: "/:path*",
};

const USERNAME = "cup1980adm";
const PASSWORD = "cup1980!passwd";

export default function middleware(request) {
  const authHeader = request.headers.get("authorization");

  if (authHeader) {
    const [scheme, encoded] = authHeader.split(" ");
    if (scheme === "Basic" && encoded) {
      // "user:pass" をデコード
      const decoded = atob(encoded);
      const sep = decoded.indexOf(":");
      const user = decoded.slice(0, sep);
      const pass = decoded.slice(sep + 1);
      if (user === USERNAME && pass === PASSWORD) {
        // 認証OK → そのまま通す
        return;
      }
    }
  }

  // 認証なし／不一致 → 401でブラウザの認証ダイアログを出す
  return new Response("Authentication required.", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Secure Area", charset="UTF-8"',
    },
  });
}
