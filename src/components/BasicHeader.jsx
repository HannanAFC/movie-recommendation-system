import { Logo } from './Logo';
import { ThemeToggle } from './ThemeToggle';

export function BasicHeader({ sticky })
{
    const clasName = `${ sticky && "sticky top-0" } z-100 pb-4 bg-linear-to-b from-white dark:from-neutral-900 from-70% to-transparent w-full`

    return (
        <header className={clasName}>
            <div className="flex flex-row items-center justify-between gap-2 bg-willow-green-200 dark:bg-willow-green-950 py-2 px-3 rounded-md shadow-s">
                <Logo />
                <ThemeToggle />
            </div>
        </header>
        );
}