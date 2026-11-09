import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('UI runtime error', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen bg-bg-soft p-6">
          <div className="mx-auto max-w-3xl rounded-card border border-warning/40 bg-white p-4 shadow-card">
            <h1 className="text-lg font-semibold text-text-primary">Interface error</h1>
            <p className="mt-2 text-sm text-text-secondary">
              The dashboard hit a runtime error. Check the browser console for the stack trace.
            </p>
            <pre className="mt-3 overflow-auto rounded-md bg-bg-soft p-3 text-xs text-warning">
              {this.state.error?.message || String(this.state.error)}
            </pre>
            <button
              type="button"
              className="mt-3 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white"
              onClick={() => window.location.reload()}
            >
              Reload
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
