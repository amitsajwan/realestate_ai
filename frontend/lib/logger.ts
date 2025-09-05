'use client';

// Comprehensive frontend logging utility

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

export interface LogContext {
  userId?: string;
  sessionId?: string;
  requestId?: string;
  component?: string;
  action?: string;
  endpoint?: string;
  method?: string;
  statusCode?: number;
  duration?: number;
  errorDetails?: any;
  metadata?: Record<string, any>;
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: LogContext;
  error?: Error;
}

class FrontendLogger {
  private logLevel: LogLevel;
  private sessionId: string;
  private logs: LogEntry[] = [];
  private maxLogs: number = 1000;
  private enableConsole: boolean;
  private enableStorage: boolean;

  constructor() {
    this.logLevel = this.getLogLevel();
    this.sessionId = this.generateSessionId();
    this.enableConsole = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_ENABLE_CONSOLE_LOGS === 'true';
    this.enableStorage = process.env.NEXT_PUBLIC_ENABLE_LOG_STORAGE === 'true';
    
    this.info('Frontend Logger initialized', {
      sessionId: this.sessionId,
      metadata: {
        logLevel: LogLevel[this.logLevel],
        enableConsole: this.enableConsole,
        enableStorage: this.enableStorage
      }
    });
  }

  private getLogLevel(): LogLevel {
    const envLevel = process.env.NEXT_PUBLIC_LOG_LEVEL?.toUpperCase();
    switch (envLevel) {
      case 'DEBUG': return LogLevel.DEBUG;
      case 'INFO': return LogLevel.INFO;
      case 'WARN': return LogLevel.WARN;
      case 'ERROR': return LogLevel.ERROR;
      default: return process.env.NODE_ENV === 'development' ? LogLevel.DEBUG : LogLevel.INFO;
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private shouldLog(level: LogLevel): boolean {
    return level >= this.logLevel;
  }

  private createLogEntry(level: LogLevel, message: string, context?: LogContext, error?: Error): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: {
        ...context,
        sessionId: this.sessionId
      },
      error
    };
  }

  private formatConsoleMessage(entry: LogEntry): string {
    const timestamp = new Date(entry.timestamp).toLocaleTimeString();
    const level = LogLevel[entry.level];
    const component = entry.context?.component ? `[${entry.context.component}]` : '';
    return `${timestamp} ${level} ${component} ${entry.message}`;
  }

  private logToConsole(entry: LogEntry): void {
    if (!this.enableConsole) return;

    const message = this.formatConsoleMessage(entry);
    const context = entry.context;
    const error = entry.error;

    switch (entry.level) {
      case LogLevel.DEBUG:
        console.debug(message, context, error);
        break;
      case LogLevel.INFO:
        console.info(message, context, error);
        break;
      case LogLevel.WARN:
        console.warn(message, context, error);
        break;
      case LogLevel.ERROR:
        console.error(message, context, error);
        break;
    }
  }

  private storeLog(entry: LogEntry): void {
    if (!this.enableStorage) return;

    this.logs.push(entry);
    
    // Maintain max logs limit
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Store in localStorage for debugging (development only)
    if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
      try {
        const recentLogs = this.logs.slice(-100); // Keep last 100 logs in localStorage
        localStorage.setItem('frontend_logs', JSON.stringify(recentLogs));
      } catch (e) {
        // Ignore localStorage errors
      }
    }
  }

  private log(level: LogLevel, message: string, context?: LogContext, error?: Error): void {
    if (!this.shouldLog(level)) return;

    const entry = this.createLogEntry(level, message, context, error);
    this.logToConsole(entry);
    this.storeLog(entry);
  }

  debug(message: string, context?: LogContext): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  info(message: string, context?: LogContext): void {
    this.log(LogLevel.INFO, message, context);
  }

  warn(message: string, context?: LogContext, error?: Error): void {
    this.log(LogLevel.WARN, message, context, error);
  }

  error(message: string, context?: LogContext, error?: Error): void {
    this.log(LogLevel.ERROR, message, context, error);
  }

  // API-specific logging methods
  logApiRequest(method: string, endpoint: string, context?: LogContext): void {
    this.info(`API Request: ${method} ${endpoint}`, {
      ...context,
      method,
      endpoint,
      action: 'api_request'
    });
  }

  logApiResponse(method: string, endpoint: string, statusCode: number, duration: number, context?: LogContext): void {
    const level = statusCode >= 400 ? LogLevel.ERROR : statusCode >= 300 ? LogLevel.WARN : LogLevel.INFO;
    this.log(level, `API Response: ${method} ${endpoint} - ${statusCode} (${duration}ms)`, {
      ...context,
      method,
      endpoint,
      statusCode,
      duration,
      action: 'api_response'
    });
  }

  logApiError(method: string, endpoint: string, error: any, context?: LogContext): void {
    this.error(`API Error: ${method} ${endpoint}`, {
      ...context,
      method,
      endpoint,
      action: 'api_error',
      errorDetails: {
        message: error.message,
        status: error.status,
        response: error.response
      }
    }, error);
  }

  // Component-specific logging methods
  logComponentMount(component: string, context?: LogContext): void {
    this.debug(`Component mounted: ${component}`, {
      ...context,
      component,
      action: 'component_mount'
    });
  }

  logComponentUnmount(component: string, context?: LogContext): void {
    this.debug(`Component unmounted: ${component}`, {
      ...context,
      component,
      action: 'component_unmount'
    });
  }

  logUserAction(action: string, component: string, context?: LogContext): void {
    this.info(`User action: ${action}`, {
      ...context,
      component,
      action: 'user_action',
      metadata: { userAction: action }
    });
  }

  logFormSubmission(formName: string, success: boolean, context?: LogContext): void {
    const level = success ? LogLevel.INFO : LogLevel.ERROR;
    this.log(level, `Form submission: ${formName} - ${success ? 'success' : 'failed'}`, {
      ...context,
      action: 'form_submission',
      metadata: { formName, success }
    });
  }

  logNavigation(from: string, to: string, context?: LogContext): void {
    this.info(`Navigation: ${from} → ${to}`, {
      ...context,
      action: 'navigation',
      metadata: { from, to }
    });
  }

  // Authentication logging
  logAuthEvent(event: string, success: boolean, context?: LogContext): void {
    const level = success ? LogLevel.INFO : LogLevel.WARN;
    this.log(level, `Auth event: ${event} - ${success ? 'success' : 'failed'}`, {
      ...context,
      action: 'auth_event',
      metadata: { authEvent: event, success }
    });
  }

  // Performance logging
  logPerformance(operation: string, duration: number, context?: LogContext): void {
    const level = duration > 5000 ? LogLevel.WARN : duration > 2000 ? LogLevel.INFO : LogLevel.DEBUG;
    this.log(level, `Performance: ${operation} took ${duration}ms`, {
      ...context,
      action: 'performance',
      duration,
      metadata: { operation }
    });
  }

  // Get logs for debugging
  getLogs(level?: LogLevel): LogEntry[] {
    if (level !== undefined) {
      return this.logs.filter(log => log.level >= level);
    }
    return [...this.logs];
  }

  // Clear logs
  clearLogs(): void {
    this.logs = [];
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('frontend_logs');
      } catch (e) {
        // Ignore localStorage errors
      }
    }
    this.info('Logs cleared');
  }

  // Export logs for debugging
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

// Create singleton instance
export const logger = new FrontendLogger();

// Utility functions for common logging patterns
export const logApiCall = (method: string, endpoint: string) => {
  const startTime = Date.now();
  logger.logApiRequest(method, endpoint);
  
  return {
    success: (statusCode: number, context?: LogContext) => {
      const duration = Date.now() - startTime;
      logger.logApiResponse(method, endpoint, statusCode, duration, context);
    },
    error: (error: any, context?: LogContext) => {
      logger.logApiError(method, endpoint, error, context);
    }
  };
};

export const logComponentLifecycle = (componentName: string) => {
  logger.logComponentMount(componentName);
  
  return () => {
    logger.logComponentUnmount(componentName);
  };
};

export const logUserInteraction = (action: string, component: string, metadata?: Record<string, any>) => {
  logger.logUserAction(action, component, { metadata });
};

// Error boundary logging
export const logErrorBoundary = (error: Error, errorInfo: any, component: string) => {
  logger.error(`Error boundary caught error in ${component}`, {
    component,
    action: 'error_boundary',
    errorDetails: {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    }
  }, error);
};

// Global error handler
if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    logger.error('Global error caught', {
      action: 'global_error',
      errorDetails: {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      }
    }, event.error);
  });

  window.addEventListener('unhandledrejection', (event) => {
    logger.error('Unhandled promise rejection', {
      action: 'unhandled_rejection',
      errorDetails: {
        reason: event.reason
      }
    });
  });
}