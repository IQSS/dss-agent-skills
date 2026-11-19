# Contributing

Submit new skills and changes through pull requests. A skill should perform a clear research task, explain when it applies, and include the supporting files needed to use it.

Start changes to an existing skill from the latest repository version and preserve other contributors' improvements. Include only the skill, supporting resources, and catalogue changes relevant to the proposal.

Keep credentials, personal paths, and machine-specific assumptions out of contributions. State required software and host capabilities in the skill's compatibility field. Prefer the user's existing project conventions to a fixed layout.

For a new skill, add its directory to `.claude-plugin/plugin.json` and an entry to `catalogue.json`. Include a useful example prompt, requirements, and expected outputs.

Run `just check` and test changed helpers or workflows on a small, appropriate example. Run `just site` to build and check the website. Describe what was tested and what remains untested in the PR. Maintainers review proposed content before merging it.

The code and skill instructions are released under the MIT license.
