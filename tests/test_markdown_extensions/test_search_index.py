from markdown import Markdown
from markdown.extensions.toc import TocExtension
from mkdocs2.markdown_extensions.search_index import SearchIndex


def test_search_index():
    md = Markdown(extensions=[TocExtension(), SearchIndex()])
    md.convert(
        """
# Lorem ipsum

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Dui nunc mattis enim ut tellus elementum
sagittis vitae.

## Ut etiam

Facilisis mauris sit amet massa vitae tortor condimentum lacinia. Gravida rutrum quisque non tellus.
Non nisi est sit amet facilisis magna.

Amet volutpat consequat mauris nunc. Sed blandit libero volutpat sed.

* Ut etiam sit amet nisl purus.
* Sed turpis tincidunt id aliquet risus.
* Mi sit amet mauris commodo quis imperdiet massa tincidunt.

Egestas maecenas pharetra convallis posuere morbi. Lobortis mattis aliquam faucibus purus.

Velit ut tortor pretium viverra. Dictum fusce ut placerat orci nulla pellentesque dignissim enim.

Blandit libero volutpat sed cras ornare arcu dui vivamus. Libero nunc consequat interdum varius.

# Risus commodo

Viverra maecenas accumsan lacus vel facilisis volutpat est.
Aenean vel elit `scelerisque` mauris pellentesque pulvinar pellentesque habitant morbi.
"""
    )
    assert md.search_index == [
        {
            "ref": "lorem-ipsum",
            "title": "Lorem ipsum",
            "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor\nincididunt ut labore et dolore magna aliqua. Dui nunc mattis enim ut tellus elementum\nsagittis vitae. ",
        },
        {
            "ref": "ut-etiam",
            "title": "Ut etiam",
            "text": "Facilisis mauris sit amet massa vitae tortor condimentum lacinia. Gravida rutrum quisque non tellus.\nNon nisi est sit amet facilisis magna. Amet volutpat consequat mauris nunc. Sed blandit libero volutpat sed. \n Ut etiam sit amet nisl purus. Sed turpis tincidunt id aliquet risus. Mi sit amet mauris commodo quis imperdiet massa tincidunt. Egestas maecenas pharetra convallis posuere morbi. Lobortis mattis aliquam faucibus purus. Velit ut tortor pretium viverra. Dictum fusce ut placerat orci nulla pellentesque dignissim enim. Blandit libero volutpat sed cras ornare arcu dui vivamus. Libero nunc consequat interdum varius. ",
        },
        {
            "ref": "risus-commodo",
            "title": "Risus commodo",
            "text": "Viverra maecenas accumsan lacus vel facilisis volutpat est.\nAenean vel elit  scelerisque ",
        },
    ]
