import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    private handleReload = () => {
        window.location.reload();
    };

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
                    <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full text-center">
                        <h2 className="text-2xl font-bold text-red-600 mb-4">哎呀，出错了！</h2>
                        <p className="text-gray-600 mb-6">
                            应用程序遇到了一些问题。请尝试刷新页面。
                        </p>
                        {this.state.error && (
                            <div className="mb-6 p-4 bg-red-50 text-left rounded text-sm text-red-800 overflow-auto max-h-40">
                                <p className="font-semibold">错误信息:</p>
                                <pre className="whitespace-pre-wrap">{this.state.error.message}</pre>
                            </div>
                        )}
                        <button
                            onClick={this.handleReload}
                            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        >
                            刷新页面
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
