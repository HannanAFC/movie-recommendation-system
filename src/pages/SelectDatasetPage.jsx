import { useEffect, useState, useRef } from 'react';
import { useBeforeUnload } from 'react-router';
import { io, Socket } from 'socket.io-client';
import axios from 'axios';
import { BasicHeader } from '../components/BasicHeader';
import { FormError } from '../components/FormError';
import { getCookie } from '../utils/getCookie';

export function SelectDatasetPage({ setDatasetSelected })
{
    const [ error, setError ] = useState( null );
    const [ dataset, setDataset ] = useState( "standard" )
    const [ availabeDatasets, setAvailableDatasets ] = useState([ ]);
    const ws = useRef( null );
    const [ downloadProgress, setDownloadProgress ] = useState( 0 );
    const [ downloadStarted, setDownloadStarted ] = useState( false );
    const [ downloadFinished, setDownloadFinished ] = useState( false );

    useEffect( ( ) =>
    {
        async function getAvailableDatasets( )
        {
                const response = await axios.get( "/api/datasets-available" )
                .catch( ( error ) =>
                {
                    if ( error.response && error.response.status === 500 )
                    {
                        setError( error.response.data.error || "Unknown server error occured." );
                    }
                    else
                    {
                        setError( "Unknown server error occured." );
                    }
                } );
                if ( response.data )
                {
                    setAvailableDatasets( response.data );
                }
            }
            getAvailableDatasets( );
    }, [ ]);

    useEffect(() => {
        if (ws.current) return; // prevent duplicate connections

        ws.current = io("http://127.0.0.1:5000/api/datasets-download-progress", {
            transports: ["websocket"],
            withCredentials: true,
            cors:
            {
                origin: "http://127.0.0.1:5174/",
            }
        });

        const socket = ws.current;

        socket.on("connect", () => {
            console.log("ws connected", socket.id);
        });

        socket.on("disconnect", () => {
            console.log("ws disconnected");
        });

        socket.on("progress_update", (data) => {
            console.log( data );
            setDownloadProgress(data.download_percentage || 0);
        });

        socket.on("progress_complete", () => {
            setDownloadProgress(100);
            setDownloadStarted(false);
            setDownloadFinished(true);
        });

        socket.on("error", (data) => {
            setError(data.error);
            console.error("Socket error:", data);
        });

        socket.onAny((event, ...args) => {
            console.log("Received event:", event, args);
        });

        return () => {
            socket.disconnect();
            ws.current = null;
        };
    }, []);

    function handleSelectChange( event )
    {
        setDataset( event.target.value );
    }

    function handleFormSubmit( event )
    {
        event.preventDefault( );
        if ( dataset )
        {
            const formData = new FormData( );
            formData.append( "dataset", dataset );
            
            async function downloadDataset( formData )
            {
                const response = await axios.postForm( "/api/datasets-select", formData,
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
                } );
                
                if ( response.data)
                {
                    setDownloadProgress( 0 );
                    setDownloadStarted( true );
                    setDownloadFinished( false );
                }
            }
            
            downloadDataset( formData );
        }
        else
        {
            setError( "Please select a dataset" );
        }
    };

    return(
        <>
            <title>WatchWok | Select a dataset</title>

            <BasicHeader />

            <div className="min-h-[calc(100vh-128px)] flex flex-col items-center justify-center gap-2 md:gap-4 max-w-300 mx-auto">
                <section className="flex flex-col gap-2 md:gap-4">
                    {
                        ( availabeDatasets && availabeDatasets.length > 0 ) ?
                            (
                                <form
                                    className="flex flex-col gap-1 md:gap-2 max-w-max"
                                    onSubmit={handleFormSubmit}
                                >
                                    <h1 className="font-bold text-3xl md:text-5xl mb-2">
                                        Select a dataset
                                    </h1>
                                    <select
                                        name="Select a dataset"
                                        id="dataset"
                                        value={dataset}
                                        onChange={handleSelectChange}
                                    >
                                        { availabeDatasets.map( (datasetItem) =>
                                            {
                                                return(
                                                    <option key={datasetItem.identifier} value={datasetItem.identifier}>{datasetItem.name}</option>
                                                );
                                            })
                                        }
                                    </select>
                                    <FormError error={error} />
                                    <span className="text-sm font-bold text-yellow-600 bg-amber-500/10 border border-yellow-600 rounded-md p-2">Note - selected datasets effect ALL users.</span>
                                    <button
                                        type="submit"
                                        className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-2 px-8 text-md font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale] mt-2"
                                        disabled={dataset === null}
                                    >
                                        Download dataset
                                    </button>
                                    {downloadStarted && (
                                        <div className="mt-4">
                                            Download progress: {downloadProgress}%
                                        </div>
                                    )}
                                </form>
                            ) : (
                                <FormError error={error} />
                            )
                    }

                    <div className="flex flex-col gap-2">
                        <h1 className="text-xl md:text-2xl font-semibold">
                            Which dataset should I choose?
                        </h1>
                        <p>
                            Datasets are what power the WatchWok recommendation system, providing alot of data related to movies - most importantly, user ratings. It is recommended to select the standard dataset, however, if you just want to test WatchWok out - the test dataset may be useful for generating recommendations more quickly. However, the recommendations may be less accurate and will feature less movies.
                        </p>
                    </div>
                </section>
            </div>
        </>
    );
}