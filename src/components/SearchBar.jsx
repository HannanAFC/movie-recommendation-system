export function SearchBar({ searchValue, onSearchValueChange, id, name, placeholder, autoComplete, borderClass, backgroundClass, textClass })
{
    function handleValueChange( event )
    {
        onSearchValueChange( event.target.value );
    }

    const borderStyling     = borderClass || "border-3 focus:border-willow-green-500 box-border"
    const backgroundStyling = backgroundClass || ""
    const textStyling       = textClass || ""

    const className = `transition-[border,color] outline-0 rounded-md p-1 ${borderStyling} ${backgroundStyling} ${textStyling}`

    return (
        <input
            id={id}
            name={name}
            type="text"
            placeholder={placeholder}
            className={className}
            value={searchValue}
            onChange={handleValueChange}
            autoComplete={autoComplete}
        />
    );
}