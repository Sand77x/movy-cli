# args is all args after sys.argv[0]
def parse(args: list[str]):
    query = []
    options = {}

    if len(args) < 1:
        return None

    if args[0] == "mv" or args[0] == "movie":
        options["media_type"] = "movie"
    elif args[0] == "tv":
        options["media_type"] = "tv"
    else:
        return None

    k = None
    for a in args[1:]:
        if k:
            options[k] = a
            k = None
            continue

        if a.startswith("--"):
            word = a[2:]
        elif a.startswith("-") and len(a) == 2:
            word = a[1:2]
        else:
            query.append(a)
            continue

        if word == "e" or word == "episode":
            k = "episode"
        elif word == "s" or word == "season":
            k = "season"
        elif word == "h" or word == "help":
            options["help"] = True
        elif word == "d" or word == "download":
            options["download"] = True
        elif word == "no-subs":
            options["no-subs"] = True
        elif word == "no-detach":
            options["no-detach"] = True

    if query:
        options["query"] = " ".join(query)
    return options
