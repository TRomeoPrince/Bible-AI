# Bible-AI translation data

## Public/open translations

Place verified public-domain or openly licensed translation JSON files in:

data/translations/

## Private user-supplied translations

Place personal, lawfully obtained translation files in:

data/private_translations/

That directory is gitignored so copyrighted texts are not accidentally committed or redistributed.

A user-supplied file does **not** automatically grant Bible-AI permission to use the text with AI. Its metadata should reflect the permissions being relied upon. If AI use is not authorized, set ai_grounding_allowed to false.

## JSON shape

{
  "translation": {
    "code": "EXAMPLE",
    "name": "Example Bible",
    "access_mode": "user_supplied_private",
    "permissions": {
      "local_storage_allowed": true,
      "ai_grounding_allowed": false,
      "caching_allowed": false,
      "redistribution_allowed": false,
      "notes": "Private local copy; verify the applicable license."
    },
    "attribution": "Required attribution here",
    "source_url": "https://example.org"
  },
  "verses": {
    "John": {
      "3": {
        "3": "Verse text here"
      }
    }
  }
}
