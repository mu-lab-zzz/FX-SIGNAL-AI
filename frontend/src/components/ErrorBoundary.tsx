import React, { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  label?: string;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          background: "#1f2937", borderRadius: 10,
          padding: 20, margin: 8,
          border: "1px solid #ef444455",
        }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#ef4444", marginBottom: 8 }}>
            ⚠ {this.props.label ?? "コンポーネント"} の読み込みに失敗しました
          </div>
          <div style={{ fontSize: 11, color: "#6b7280", fontFamily: "monospace",
            whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
            {this.state.error.message}
          </div>
          <button
            onClick={() => this.setState({ error: null })}
            style={{
              marginTop: 12, background: "#374151", border: "none",
              borderRadius: 6, color: "#d1d5db",
              padding: "6px 14px", fontSize: 12, cursor: "pointer",
            }}
          >
            再試行
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
