import { Link } from 'react-router';

export function LoginLink( )
{
    return (
        <Link to={"/login"} className="bg-willow-green-600 dark:bg-willow-green-400 text-white dark:text-black py-2 px-4 text-2xl font-semibold rounded-xl">
            Login
        </Link>
    );
}