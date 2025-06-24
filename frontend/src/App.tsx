// frontend/src/App.tsx
import React from 'react';
import { ChatFlow } from './components/ChatFlow';
import { Live2DViewer } from './components/Live2DViewer'; // ⬅️ 新增
import './App.css';

/**
 * 全局错误边界组件
 */
interface ErrorBoundaryState {
  hasError: boolean;
  errorInfo?: string;
}

export class ErrorBoundary extends React.Component<React.PropsWithChildren<{}>, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, errorInfo: error.message };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('ErrorBoundary 捕获到错误:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-gray-100 p-4">
          <div className="bg-white p-6 rounded-lg shadow-md text-red-600">
            <h1 className="text-2xl mb-2">很抱歉，出现了错误。</h1>
            <p>错误信息：{this.state.errorInfo}</p>
          </div>
        </div>
      );
    }
    return <>{this.props.children}</>;
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <header className="mb-6">
          <h1 className="text-3xl font-bold">AI 虚拟主播演示</h1>
        </header>
        {/* ⬇️ 改为左右布局 */}
        <main className="flex w-full max-w-5xl gap-4">
          <div className="flex-1">
            <ChatFlow />
          </div>
          <div className="w-[400px] h-[600px] bg-white rounded shadow p-2">
            <Live2DViewer />
          </div>
        </main>
      </div>
    </ErrorBoundary>
  );
}
