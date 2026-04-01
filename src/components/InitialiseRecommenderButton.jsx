import axios from "axios";
import { FormError } from "./FormError";
import { useState } from "react";

export function InitialiseRecommenderButton({ user, showNotification })
{
    const [ error, setError ] = useState( null );

    async function sendInitialiseRequest( )
    {
        const response = await axios.post("/api/recommendations/initialise")
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
            showNotification(
                {
                    isOpen: true,
                    type: "success",
                    content: response.data.message,
                    dismissable: true,
                    timeout: 4000
                }
            );
        }
    }

    function handleInitialise( )
    {
        sendInitialiseRequest( );
    }

    return (
        <>
            <button
                className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-1 px-4 text-sm font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale]"
                onClick={handleInitialise}
            >
                Initialise
            </button>
            <FormError error={error} />
        </>
    );
}