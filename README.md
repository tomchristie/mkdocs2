# MkDocs2

This repository is exploring the design of a possible next iteration of `mkdocs`.

I think we've got some scope to make mkdocs both simpler, but also more powerful.
I'd like it to be suitable for a wider range of static site generation.

This isn't particularly intended for external use yet, but for me to have
a public working space for progressing the project.

**mkdocs.yml**:

```yaml
build:
    url: https://www.example.com/
    input_dir: docs
    template_dir: templates
    output_dir: build

nav:
    Home: index.md
    Page A: page-a.md
    Page B: page-b.md
    Topics:
        Topic A: topics/topic-a.md
        Topic B: topics/topic-b.md
        Topic C: topics/topic-c.md

convertors:
    - mkdocs2.convertors:MarkdownPages
    - mkdocs2.convertors:StaticFiles
    - mkdocs2.convertors:CodeHighlight
```
