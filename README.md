# sources-bot
Bot that identifies other sources of news for a story.  

## Current Development Branch
The current development branch is [split_components](https://github.com/michardy/sources-bot/tree/split_components).  This is also the code powering /u/sourcesbot on reddit and https://sourcesbot.com

## How it works

1. Current news sites are queried for current articles. (This is information is periodically refreshed as it goes out of date.)
2. Editorials are identified.
3. Titles of current news sites are broken down to find people, places, organizations, other nouns, and verbs.  Headlines are also futher scanned for mandated places and attributed speakers.  
4. The source is loaded and the title is found.  
5. The title of the news story is broken down to find people, places, organizations, other nouns, and verbs.  Headlines are also futher scanned for mandated places and attributed speakers.  
6. The news stories are checked to see the degree that they overlap.  Stoies that overlap more than a certain amount are displayed. 
