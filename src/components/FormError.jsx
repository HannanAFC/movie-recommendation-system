export function FormError({ error })
{
    const className = `overflow-hidden transition-[height,opacity] duration-300 ease-in-out ${ error ? "max-h-[10.5] opacity-100" : "max-h-0 opacity-0" }`;

    return (
        <div className={className}>
            <span className="p-2 flex flex-row items-center justify-center bg-red-500/10 border-red-500 border rounded-md transition-[height,opacity] text-red-500 text-sm" aria-label="Form error">
                {error}
            </span>
        </div>
    )
}