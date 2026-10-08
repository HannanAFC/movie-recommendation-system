import { useState, useEffect } from 'react';
import { apiClient } from '../utils/apiClient';
import { SearchBar } from './SearchBar';
import { FormError } from './FormError';

export function MovieSearchBar({ setMovies })
{
    const [ searchValue, setSearchValue ] = useState( "" );
    const [ error, setError ]             = useState( null );

    function handleSearchValueChange( value )
    {
        setSearchValue( value );

        if ( value.trim() === "" )
        {
            setMovies([ ]);
            setError( null );
        }
    }

    useEffect( ( ) =>
    {
        const trimmedSearchValue = searchValue.trim();
        if ( trimmedSearchValue === "" )
        {
            return;
        }

        const controller = new AbortController();

        const timeoutId = setTimeout( async () =>
        {
            const response = await apiClient.get( `/api/movies/search?q=${encodeURIComponent(trimmedSearchValue)}`,
            {
                signal: controller.signal
            } )
            .catch( ( error ) =>
            {
                if ( error.response.status === 500 )
                {
                    setError( "Internal server error." );
                }
                else
                {
                    setError( error.response.data.error );
                }
                
                setMovies([ ]);
            } );

            if ( response && response.data && response.data.results )
            {
                setMovies( response.data.results );
            }
            else
            {
                setMovies([ ]);
            }

            if ( response && response.data.tmdb_enrichment_available && response.data.tmdb_enrichment_available === false )
            {
                setError( "TMDB metadata enrichment not available." );
            }
            else
            {
                setError( null );
            }
        }, 400 );

        // clean up code to run before next search.
        return ( ) =>
        {
            clearTimeout( timeoutId );
            controller.abort( );
        };

    }, [ searchValue, setMovies ] );

    return (
        <div
            className="flex flex-col w-full sticky top-200"
        >
            <SearchBar
                searchValue={searchValue}
                onSearchValueChange={handleSearchValueChange}
                id="movies"
                name="Search for a movies"
                placeholder="Search for a movie..."
                borderClass="border-4 border-willow-green-400 dark:border-willow-green-700 focus:border-willow-green-600"
                backgroundClass="bg-willow-green-100 dark:bg-willow-green-800/30"
                textClass="focus:placeholder:text-willow-green-800 dark:focus:placeholder:text-willow-green-100"
            />
            <FormError
                error={error}
            />
        </div>
    );
}