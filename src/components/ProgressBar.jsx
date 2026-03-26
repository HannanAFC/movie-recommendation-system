export function ProgressBar({ progress })
{
    return (
        <div
            className="h-6 w-full bg-willow-green-200 dark:bg-willow-green-900 flex rounded-full overflow-hidden dark:border-2 dark:border-willow-green-800 shadow-s"
        >
            <div
                className="bg-willow-green-600 dark:bg-willow-green-400 h-full rounded-lg shadow-m transition-[width] duration-150" 
                style={{ width: `${progress}%` }}
            >
            </div>
        </div>
    );
}