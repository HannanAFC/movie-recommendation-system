import TMDBLogo from '../assets/images/tmdb-logo.png';
import { LogoutButton } from './LogoutButton';

export function Footer({ setUser })
{
    return (
        <div className="w-full flex flex-col gap-2 p-4 mt-3 md:mt-5 bg-willow-green-200 dark:bg-willow-green-900 rounded-md shadow-m text-md">
            <div className="flex flex-col md:flex-row gap-2 justify-between items-center">
                <p>
                    @2026 WatchWok
                </p>
                <p>
                    Powered by TMDB and MovieLens
                </p>
            </div>
            <div className="flex flex-col-reverse md:flex-row gap-2 justify-between items-center">
                <LogoutButton setUser={setUser} />
                <img className="h-5 w-fit" src={TMDBLogo} alt="TMDB Logo" />
            </div>
        </div>
    );
}