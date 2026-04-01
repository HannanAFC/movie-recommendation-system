import { useState } from 'react';
import axios from 'axios';
import { FormError } from '../components/FormError';
import { getCookie } from '../utils/getCookie';
import { FormSuccess } from './FormSuccess';
import { SearchBar } from '../components/SearchBar'

export function TmdbApiKeyForm({ tmdbApiKeyStatus, setTmdbApiKeyStatus })
{
    const [ value, setValue ]                   = useState( "" );
    const [ error, setError ]                   = useState( null );
    const [ successMessage, setSuccessMessage ] = useState( tmdbApiKeyStatus.api_key_set === true && tmdbApiKeyStatus.api_key_valid === true ? "API key is already saved and has been validated." : null );

    function handleFormSubmit( event )
    {
        event.preventDefault( );
        if ( value.trim( ) === "" )
        {
            setError( "Please enter an API key." )
            setSuccessMessage( null );
        }
        else
        {
            const formData = new FormData( );
            formData.append( "api_key", value );

            async function sumbitApiKey( formData )
            {
                const response = await axios.postForm( "/api/tmdb-api-key", formData,
                {
                    headers:
                    {
                        "X-CSRF-TOKEN": getCookie( "csrf_access_token" )
                    }
                } )
                .catch( ( error ) =>              
                {
                    if ( error.response && error.response.status === 500 )
                    {
                        setError( "Internal server error." );
                    } else
                    {
                        setError( error.response.data.error || "Unknown server error occured." );
                    }
                    setSuccessMessage( null );
                } );

                if ( response && response.data && response.data.tmdb )
                {
                    setTmdbApiKeyStatus( response.data.tmdb );
                    setSuccessMessage( response.data.message );
                    setError( null );
                }
            }
            
            sumbitApiKey( formData );
        }
    }

    return (
        <div className="bg-willow-green-300 dark:bg-willow-green-800 p-4 rounded-md shadow-l">
            <form
                className="flex flex-col max-w-max md:min-w-max"
                onSubmit={handleFormSubmit}
            >
                <h1 className="font-bold text-3xl md:text-5xl mb-3 md:mb-4">
                    Enter your API key
                </h1>
                <SearchBar
                    searchValue={value}
                    onSearchValueChange={setValue}
                    id="tmdb_api_key"
                    name="TMDB API key"
                    placeholder="TMDB API key"
                    autoComplete={"off"}
                />
                <FormSuccess message={successMessage} />
                <FormError error={error} />
                <button
                    type="submit"
                    className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-2 px-8 text-md font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale]"
                >
                    Validate key
                </button>
            </form>
        </div>
    )
}