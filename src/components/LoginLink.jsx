import { Link } from 'react-router';

export function LoginLink( )
{
    return (
        <Link to={"/login"} className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-2 px-8 text-md font-semibold rounded-md flex items-center shadow-m transition-[background-color,scale]">
            Login
        </Link>
    );
}