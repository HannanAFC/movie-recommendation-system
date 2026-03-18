import { ThemeToggle } from "./ThemeToggle";

export function BasicHeader( )
{
    return (
        <header className="sticky top-0 pb-4 bg-linear-to-b from-white dark:from-neutral-900 from-70% to-transparent w-full">
            <div className="flex flex-row items-center justify-between gap-2 bg-willow-green-200 dark:bg-willow-green-950 py-2 px-3 rounded-2xl">
                <h1 className="text-3xl md:text-4xl font-extrabold">
                    <span className="text-willow-green-900 dark:text-willow-green-500">Watch</span>
                    <span className="text-willow-green-500 dark:text-willow-green-300">Wok</span>
                </h1>
                <ThemeToggle />
            </div>
        </header>
        );
}