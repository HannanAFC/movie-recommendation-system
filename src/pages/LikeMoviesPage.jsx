import { useState, useEffect } from 'react';
import { BasicHeader } from '../components/BasicHeader';
import { MovieSearchBar } from '../components/MovieSearchBar';
import { MovieGrid } from '../components/MovieGrid';
import '../types/movies';

export function LikeMoviesPage({ setNeedsToSelectMovies, likedMovies, setLikedMovies })
{
    /** @type {[MovieSearchResult[], React.Dispatch<React.SetStateAction<MovieSearchResult[]>>]} */
    const [ movies, setMovies ] = useState([ ]);
    const [ canContinue, setCanContinue ] = useState( false );

    function handleContinueClick( )
    {
        if ( canContinue )
        {
            setNeedsToSelectMovies( false );
        }
    }

    useEffect( ( ) =>
    {
        console.log( movies );
    }, [ movies ] )
    
    return(
        <>
            <title>WatchWok | Select you favourites</title>
            
            <BasicHeader sticky={false} />

            <div
                className="sticky top-0 z-100 pt-1 pb-4 bg-linear-to-b from-white dark:from-neutral-900 from-70% to-transparent w-full"
            >
                <div
                    className="flex w-full p-2 bg-willow-green-200 dark:bg-willow-green-900 rounded-md shadow-m items-center gap-2"
                >
                    <MovieSearchBar
                        setMovies={setMovies}
                    />
                    <button
                        onClick={handleContinueClick}
                        disabled={!canContinue}
                        className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-2 px-8 text-md font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale] mt-2 max-w-40 self-center disabled:bg-neutral-400 disabled:cursor-not-allowed"
                    >
                        Continue
                    </button>
                </div>
            </div>

            <div className="min-h-[calc(100vh-128px)] flex flex-col items-center gap-2 md:gap-4 max-w-300 mx-auto">
                <section className="flex flex-col gap-2 md:gap-16 w-full">
                    <MovieGrid movies={movies} setCanContinue={setCanContinue} likedMovies={likedMovies} setLikedMovies={setLikedMovies} />
                </section>
            </div>
        </>
    );
}