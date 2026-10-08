import { useEffect, useState } from 'react';
import { apiClient } from '../utils/apiClient';
import { socket } from '../components/socket';
import { FormError } from '../components/FormError';
import { getCookie } from '../utils/getCookie';
import { ProgressBar } from './ProgressBar';

export function DatasetSelectForm({ setDatasetSelected })
{
    const [ error, setError ] = useState( null );
    const [ dataset, setDataset ] = useState( "standard" )
    const [ availabeDatasets, setAvailableDatasets ] = useState([ ]);
    const [ downloadProgress, setDownloadProgress ] = useState( 0 );
    const [ downloadStarted, setDownloadStarted ] = useState( false );
    const [ downloadFinished, setDownloadFinished ] = useState( false );

    useEffect( ( ) =>
    {
        socket.nsp = "/api/datasets-download-progress";
        socket.connect( );

        socket.on( "connect", ( ) =>
        {
            console.log( "Connected to socket" );
        } )

        socket.on( "disconnect", ( ) =>
        {
            console.log( "Disconnected from socket" );
        } )

        socket.on( "datasets_download_start", ( data ) =>
        {
            console.log( "Download started" );
            setDownloadProgress( 0 );
            setDownloadStarted( true );
            setDownloadFinished( false );
        } );

        socket.on( "datasets_download_progress", ( data ) =>
        {
            setDownloadProgress( data.download_percentage );
            setDownloadStarted( true );
            setDownloadFinished( false );
        } );

        socket.on( "datasets_download_finish", ( data ) =>
        {
            console.log( "Download finished" );
            setDownloadProgress( 100 );
            setDownloadStarted( false );
            setDownloadFinished( true );
            setDatasetSelected( true ); 
        } )

        return ( ) =>
        {
            socket.disconnect( );
        };
    }, [ ] );

    useEffect( ( ) =>
    {
        async function getAvailableDatasets( )
        {
                const response = await apiClient.get( "/api/datasets-available" )
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
                const response = await apiClient.postForm( "/api/datasets-select", formData,
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

                if ( response && response.data )
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

    return (
        <div className="bg-willow-green-300 dark:bg-willow-green-800 p-4 rounded-md shadow-l">
            {
                ( availabeDatasets && availabeDatasets.length > 0 ) ?
                (
                    <form
                        className="flex flex-col gap-1 md:gap-2 max-w-max md:min-w-max"
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
                        <span className="text-sm font-bold text-yellow-700 dark:text-yellow-600 bg-amber-200/60 dark:bg-amber-500/10 border border-yellow-700 dark:border-yellow-600 rounded-md p-2">Note - selected datasets effect ALL users.</span>
                        <button
                            type="submit"
                            className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-2 px-8 text-md font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale] mt-2"
                            disabled={dataset === null}
                        >
                            Download dataset
                        </button>
                        <div className={downloadStarted == true ? "transition-[opacity,height] opacity-100 max-h-9" : "transition-[opacity,height]  opacity-0 max-h-0" }>
                            <ProgressBar progress={downloadProgress} />
                        </div>
                        <div className={downloadFinished == true ? "transition-[opacity,height] opacity-100 max-h-6" : "transition-[opacity,height] opacity-0 max-h-0"}>
                            Download successful.
                        </div>
                    </form>
                ) : (
                    <FormError error={error} />
                )
            }
        </div>
    );
}