import { useState } from 'react';
import axios from 'axios';
import { FormError } from './FormError';

export function CreateRecommendationButton({ setRecommendations })
{
    const [ error, setError ] = useState( null );

    async function createRecommendations( )
    {
        const response = await axios.post( "/api/recommendations/create" )
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
        } );

        if ( response && response.data )
        {
            setRecommendations( response.data.recommendation_set.movies );
        }
    }

    function handleButtonClick( )
    {
        createRecommendations( );
    }

    return(
        <>
            <button
                onClick={handleButtonClick}
                className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-1 px-4 text-sm font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale]"
            >
                Get recommendations
            </button>
            <FormError error={error} />
        </>
    );
}