export function ThemeToggle( )
{
    function toggleTheme( )
    {
        if ( document.documentElement.classList.contains( "dark" ) )
        {
            localStorage.theme = "light";
            document.documentElement.classList.remove( "dark" );
        }
        else
        {
            localStorage.theme = "dark";
            document.documentElement.classList.add( "dark" );
        }
    }

    return (
        <button
            onClick={toggleTheme}
            className="cursor-pointer shadow-s rounded-full p-1 bg-willow-green-300 dark:bg-willow-green-900"
        >
            <svg className="w-7 h-7 md:w-8 md:h-8 fill-black dark:fill-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path d="M512 320C512 214 426 128 320 128L320 512C426 512 512 426 512 320zM64 320C64 178.6 178.6 64 320 64C461.4 64 576 178.6 576 320C576 461.4 461.4 576 320 576C178.6 576 64 461.4 64 320z"/></svg>
        </button>
    );
}