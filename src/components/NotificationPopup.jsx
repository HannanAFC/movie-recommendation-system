import { useEffect, useRef, useState } from 'react';

/**
 * @param {
 * {
 *   type: "success" | "warning" | "error",
 *   content: React.ReactNode,
 *   dismissable?: boolean,
 *   timeout?: number | null,
 *   isOpen: boolean,
 *   onClose: () => void
 * }} props
 */
export function NotificationPopup(
    {
        type,
        content,
        dismissable = true,
        timeout = null,
        isOpen,
        onClose
    }
)
{
    const [ shouldRender, setShouldRender ] = useState( isOpen );
    const [ isVisible, setIsVisible ] = useState( false );
    const timeoutRef = useRef( null );
    const closeTimerRef = useRef( null );

    const typeClasses =
    {
        success: "bg-emerald-100 border-emerald-300 text-emerald-900 dark:bg-emerald-900 dark:border-emerald-700 dark:text-emerald-100",
        warning: "bg-amber-100 border-amber-300 text-amber-900 dark:bg-amber-900 dark:border-amber-700 dark:text-amber-100",
        error:   "bg-red-100 border-red-300 text-red-900 dark:bg-red-900 dark:border-red-700 dark:text-red-100"
    };

    function clearTimers( )
    {
        if ( timeoutRef.current )
        {
            clearTimeout( timeoutRef.current );
            timeoutRef.current = null;
        }

        if ( closeTimerRef.current )
        {
            clearTimeout( closeTimerRef.current );
            closeTimerRef.current = null;
        }
    }

    function startClose( )
    {
        clearTimers( );
        setIsVisible( false );

        closeTimerRef.current = setTimeout( ( ) =>
        {
            setShouldRender( false );
            onClose( );
        }, 300 );
    }

    useEffect( ( ) =>
    {
        clearTimers( );

        if ( isOpen )
        {
            setShouldRender(true);

            requestAnimationFrame( ( ) =>
            {
                setIsVisible( true );
            } );

            if ( timeout && timeout > 0 )
            {
                timeoutRef.current = setTimeout( ( ) =>
                {
                    startClose( );
                }, timeout );
            }
            else if (shouldRender)
            {
                setIsVisible(false);

                closeTimerRef.current = setTimeout(() =>
                {
                    setShouldRender(false);
                }, 300);
            }
        }

        return ( ) =>
        {
            clearTimers( );
        };
    }, [ isOpen, timeout ]);

    if (!shouldRender)
    {
        return null;
    }

    return (
        <div
            className={[
                "fixed top-4 right-4 z-200 max-w-sm w-[calc(100vw-2rem)]",
                "transition-transform transition-opacity duration-300 ease-out",
                isVisible ? "translate-x-0 opacity-100" : "translate-x-[120%] opacity-0"
            ].join(" ")}
            aria-live="polite"
            aria-atomic="true"
        >
            <div
                className={[
                    "border rounded-md shadow-lg p-4 flex items-start gap-3",
                    typeClasses[type]
                ].join(" ")}
                role={type === "error" ? "alert" : "status"}
            >
                <div className="flex-1 text-sm">
                    {content}
                </div>

                {
                    dismissable &&
                    <button
                        type="button"
                        aria-label="Dismiss notification"
                        onClick={startClose}
                        className="shrink-0 rounded-md p-1 cursor-pointer hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 640 640"
                            className="w-4 h-4 fill-current"
                        >
                            <path d="M183 183C192.4 173.6 207.6 173.6 217 183L320 286.1L423 183C432.4 173.6 447.6 173.6 457 183C466.4 192.4 466.4 207.6 457 217L353.9 320L457 423C466.4 432.4 466.4 447.6 457 457C447.6 466.4 432.4 466.4 423 457L320 353.9L217 457C207.6 466.4 192.4 466.4 183 457C173.6 447.6 173.6 432.4 183 423L286.1 320L183 217C173.6 207.6 173.6 192.4 183 183z" />
                        </svg>
                    </button>
                }
            </div>
        </div>
    );
}