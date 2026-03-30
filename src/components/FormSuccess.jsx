export function FormSuccess({ message })
{
    const className = `overflow-hidden transition-[height,opacity] duration-300 ease-in-out ${ message ? "max-h-[10.5] opacity-100 block" : "max-h-0 opacity-0 hidden" }`;

    return (
        <div className={className}>
            <span className="p-2 flex flex-row items-center justify-center bg-willow-green-500/10 border-willow-green-500 border rounded-md transition-[height,opacity] text-willow-green-500text-sm max-w-max mb-1 md:mb-2" aria-label="Form success message">
                {message}
            </span>
        </div>
    )
}