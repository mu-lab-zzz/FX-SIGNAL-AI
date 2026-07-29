import React, { useState } from "react";
import { useAuth } from "../hooks/useAuth";

interface Props {
  onClose: () => void;
}

type Mode = "login" | "register";

export const AuthModal: React.FC<Props> = ({ onClose }) => {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, displayName);
      }
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: "#111827",
    border: "1px solid #374151",
    borderRadius: 8,
    padding: "10px 14px",
    color: "#f3f4f6",
    fontSize: 14,
    boxSizing: "border-box",
    outline: "none",
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "#00000099",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#1f2937",
          borderRadius: 16,
          padding: 32,
          width: 360,
          maxWidth: "90vw",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ fontSize: 20, fontWeight: 800, color: "#f3f4f6", marginBottom: 24 }}>
          {mode === "login" ? "ログイン" : "アカウント作成"}
        </div>

        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {mode === "register" && (
            <input
              placeholder="表示名"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              style={inputStyle}
            />
          )}
          <input
            type="email"
            placeholder="メールアドレス"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="パスワード"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            style={inputStyle}
          />

          {error && <div style={{ fontSize: 13, color: "#ef4444" }}>{error}</div>}

          <button
            type="submit"
            disabled={loading}
            style={{
              background: "#1d4ed8",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "12px 0",
              fontSize: 15,
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "処理中..." : mode === "login" ? "ログイン" : "登録"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 16, fontSize: 13, color: "#9ca3af" }}>
          {mode === "login" ? (
            <>アカウントをお持ちでない方は
              <button
                onClick={() => setMode("register")}
                style={{ background: "none", border: "none", color: "#3b82f6", cursor: "pointer", fontSize: 13 }}
              >こちら</button>
            </>
          ) : (
            <>既にアカウントをお持ちの方は
              <button
                onClick={() => setMode("login")}
                style={{ background: "none", border: "none", color: "#3b82f6", cursor: "pointer", fontSize: 13 }}
              >ログイン</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
