import { BasicHeader } from '../components/BasicHeader';
import { DatasetSelectForm } from '../components/DatasetSelectForm';
import { Footer } from '../components/Footer';
import { TmdbApiKeyForm } from '../components/TmdbApiKeyForm';

export function OnboardingPage({ setOnboardingComplete, datasetSelected, setDatasetSelected, tmdbApiKeyStatus, setTmdbApiKeyStatus, setUser })
{   
    const canContinue =
    tmdbApiKeyStatus?.api_key_set &&
    tmdbApiKeyStatus?.api_key_valid &&
    datasetSelected;

    function handleContinueClick( )
    {
        if ( canContinue )
        {
            setOnboardingComplete( true );
        }
    }

    return(
        <>
            <title>WatchWok | Select a dataset</title>

            <BasicHeader sticky={true} />

            <div className="min-h-[calc(100vh-128px)] flex flex-col items-center justify-center gap-2 md:gap-4 max-w-300 mx-auto">
                <section className="flex flex-col gap-2 md:gap-16">
                    <div className="flex flex-col md:flex-row gap-2 md:gap-16">
                        <TmdbApiKeyForm tmdbApiKeyStatus={tmdbApiKeyStatus} setTmdbApiKeyStatus={setTmdbApiKeyStatus} />

                        <div className="flex flex-col gap-2">
                            <h1 className="text-xl md:text-2xl font-semibold">
                                What is a TMDB API key and why do I need it?
                            </h1>
                            <p>
                                The TMDB API is what powers this app. It's what supplies all the movie information that you see. It is necessary to have a good experience using the app. You can get an API key easily <a href="https://developer.themoviedb.org/docs/getting-started">here</a>. Once you've got it, simply enter it here!
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-col md:flex-row gap-2 md:gap-16">
                        <DatasetSelectForm datasetSelected={datasetSelected} setDatasetSelected={setDatasetSelected} />

                        <div className="flex flex-col gap-2">
                            <h1 className="text-xl md:text-2xl font-semibold">
                                Which dataset should I choose?
                            </h1>
                            <p>
                                Datasets are what power the WatchWok recommendation system, providing alot of data related to movies - most importantly, user ratings. It is recommended to select the standard dataset, however, if you just want to test WatchWok out - the test dataset may be useful for generating recommendations more quickly. However, the recommendations may be less accurate and will feature less movies.
                            </p>
                        </div>
                    </div>
                   <button
                        onClick={handleContinueClick}
                        disabled={!canContinue}
                        className="active:scale-95 cursor-pointer justify-center bg-willow-green-600 hover:bg-willow-green-700 active:bg-willow-green-800 dark:active:bg-willow-green-200 dark:hover:bg-willow-green-300 dark:bg-willow-green-400 text-white dark:text-black py-2 px-8 text-md font-semibold rounded-md flex items-center shadow-md transition-[background-color,scale] mt-2 max-w-40 self-center disabled:bg-neutral-400"
                    >
                        Continue
                    </button>
                </section>
                <Footer setUser={setUser} />
            </div>
        </>
    );
}