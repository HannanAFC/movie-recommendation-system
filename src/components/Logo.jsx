import { Link } from 'react-router';
import LogoIcon from '../assets/icons/logo-nochopsticks.png';

export function Logo( )
{
    return (
        <Link className="text-3xl md:text-4xl font-extrabold flex flex-row items-center gap-2" to="/">
            <img className="h-14 w-14" alt="Watch WokLogo" src={LogoIcon} />
            <div className="" aria-label="WatchWok">
                <span className="text-willow-green-900 dark:text-willow-green-500">Watch</span>
                <span className="text-willow-green-500 dark:text-willow-green-300">Wok</span>
            </div>
        </Link>
    );
} 