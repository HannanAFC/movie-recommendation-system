import { useState, useCallback } from 'react';

/**
 * @typedef {"success" | "warning" | "error"} NotificationType
 */

/**
 * @typedef {Object} NotificationState
 * @property {boolean} isOpen
 * @property {NotificationType} type
 * @property {React.ReactNode} content
 * @property {boolean} dismissable
 * @property {number | null} timeout
 */

/**
 * Hook for controlling a single page-level notification component.
 */
export function useNotification()
{
    /** @type {[NotificationState, React.Dispatch<React.SetStateAction<NotificationState>>]} */
    const [ notification, setNotification ] = useState({
        isOpen: false,
        type: "success",
        content: null,
        dismissable: true,
        timeout: null
    });

    /**
     * @param {{
     *   type: NotificationType,
     *   content: React.ReactNode,
     *   dismissable?: boolean,
     *   timeout?: number | null
     * }} options
     */
    const showNotification = useCallback(({
        type,
        content,
        dismissable = true,
        timeout = null
    }) =>
    {
        setNotification({
            isOpen: true,
            type,
            content,
            dismissable,
            timeout
        });
    }, []);

    const hideNotification = useCallback(() =>
    {
        setNotification((prev) => ({
            ...prev,
            isOpen: false
        }));
    }, []);

    return {
        notification,
        showNotification,
        hideNotification
    };
}