# MkDocs2

This repository is exploring the design of a possible next iteration of `mkdocs`.

I think we've got some scope to make mkdocs both simpler, but also more powerful.
I'd like it to be suitable for a wider range of static site generation.

This isn't particularly intended for external use yet, but for me to have
a public working space for progressing the project.

**mkdocs.yml**:

```yaml
site:
    name: Example
    url: https://www.example.com/

build:
    input_dir: docs
    output_dir: site
    template_dir: templates

nav:
    - Homepage: index.md
    - Topics:
        - Section A: topics/a.md
        - Section B: topics/b.md

convertors:
    markdown:
        class: mkdocs2.convertors.MarkdownConvertor
        patterns:
            - **.md
    html:
        class: mkdocs2.convertors.TemplateConvertor
        patterns:
            - **.html
```
