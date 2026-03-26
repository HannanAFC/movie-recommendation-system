import { BasicHeader } from '../components/BasicHeader';
import { DatasetSelectForm } from '../components/DatasetSelectForm';

export function SelectDatasetPage({ setDatasetSelected })
{

    return(
        <>
            <title>WatchWok | Select a dataset</title>

            <BasicHeader />

            <div className="min-h-[calc(100vh-128px)] flex flex-col items-center justify-center gap-2 md:gap-4 max-w-300 mx-auto">
                <section className="flex flex-col md:flex-row gap-2 md:gap-16">
                    <DatasetSelectForm setDatasetSelected={setDatasetSelected} />

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