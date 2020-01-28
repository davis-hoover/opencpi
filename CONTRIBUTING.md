[//]: # (These are reference links used in the body of this document and get
         stripped out when the markdown processor does its job. The blank lines
         before and after these reference links are important for portability
         across different markdown parsers.)

[groupurl]: <https://gitlab.com/opencpi>

[groupbuglist]: <https://gitlab.com/groups/opencpi/-/issues?scope=all&utf8=%E2%9C%93&state=opened&label_name[]=type%3A%3Abug>

[groupissuelist]: <https://gitlab.com/groups/opencpi/-/issues>

[groupmr]: <https://gitlab.com/groups/opencpi/-/merge_requests>

[opencpiurl]: <https://gitlab.com/opencpi/opencpi>

[buglist]: <https://gitlab.com/opencpi/opencpi/issues?label_name%5B%5D=type%3A%3Abug>

[issuelist]:  <https://gitlab.com/opencpi/opencpi/issues>

[mr]:  <https://gitlab.com/opencpi/opencpi/merge_requests>

[newissue]: <https://gitlab.com/opencpi/opencpi/issues/new>

[ospgroup]: <https://gitlab.com/opencpi/osp>

[srcinstall]: <https://opencpi.gitlab.io/releases/develop/docs/OpenCPI_Installation.pdf>

[rpminstall]: <https://opencpi.gitlab.io/releases/develop/docs/RPM_Installation_Guide.pdf>


# Contributing to OpenCPI
First off, thanks for taking the time to read this document and contribute!

The following is a set of guidelines for contributing to OpenCPI. These
are mostly guidelines, not rules. Use your best judgement and feel free to
propose changes to this document in a merge request.

Contributing to OpenCPI helps improve the framework, adds support for
new devices and platforms, and components and applications for others to use,
build on, and understand -- all of which makes OpenCPI more attractive, expands
the community, and makes it more valuable to users. The framework maintainers
will make every feasible effort to incorporate all contributions, subject to the
suitability of the contributions and the time available to review and accept
them.

**All contributions become part of OpenCPI, subject to the LGPLv3 license,
unless other arrangements are specifically made (which is rare).**

## Table of Contents
- [What to Know Before Getting Started](#what-to-know-before-getting-started)
- [Types of Contributions](#types-of-contributions)
  - [Contributing to Existing Projects](#contributing-to-existing-projects)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Submitting Bug Fixes](#submitting-bug-fixes)
    - [Submitting Enhancements or New Features](#submitting-enhancements-or-new-features)
    - [Merge Requests](#merge-requests)
  - [Contributing Projects](#contributing-projects)
    - [Applications and Components](#applications-and-components)
    - [OpenCPI System Support Projects (OSP)](#opencpi-system-support-projects-osp)
- [Additional Resources](#additional-resources)
  - [Style Guides](#style-guides)
  - [Branching Strategy](https://gitlab.com/opencpi/opencpi/wikis/Gitlab-Branching-and-Workflow)
  - [Issue and Merge Request Labels](https://gitlab.com/opencpi/opencpi/wikis/issue-labels)
  - [Versioning](#versioning)

# What to Know Before Getting Started
Before investing time on a contribution it is a good idea to find out if anyone
is already working on the same or similiar thing by using the
[OpenCPI Issue List][groupissuelist]. The OpenCPI Issue List contains issues for
every project that exists in the [OpenCPI GitLab Group][groupurl]. Another source of
information is the email discussion list at discuss@lists.opencpi.org. To post
on this list you must subscribe to it at http://lists.opencpi.org.

OpenCPI uses the [Git flow](https://gitlab.com/opencpi/opencpi/wikis/Gitlab-Branching-and-Workflow)
branching strategy.

# Types of Contributions
While many developers work on fixing bugs and creating new features, there is
a wide array of items non-programmers can help impove upon. If you're here,
you probably already have an idea of something you'd like to work on.
Contributions to OpenCPI generally fall into one of two categories. Those that
involve code changes and those that don't.

Contributions are either made to
[existing projects](#contributing-to-existing-projects) (found [here][groupurl]), or are new
[contributed projects](#contributing-projects).

All contributions which add or modify code are proposed using the standard
GitLab [forking and merge request process](https://docs.gitlab.com/ee/workflow/forking_workflow.html).
Further guidelines, can be found in the [Merge Requests](#merge-requests)
section.

>>>
**All contributions become part of OpenCPI, subject to the LGPLv3 license,
unless other arrangements are specifically made (which is rare).**
>>>

Contributions that involve code changes are usually:
- Changes to the core repository of OpenCPI consisting of:
  - Bug fixes and enhancements to the framework software
  - Bug fixes and enhancements to the built-in projects
- Contributed projects consisting of:
  - Useful/reusable components, workers and tests
  - Useful applications, either simply for reference or as interesting
    baselines or examples
- Contributed projects that are OpenCPI System Support Projects (OSP) consisting of:
  - HDL devices, cards, and platforms
  - HDL assemblies and applications for testing/exercising the platform and/or
    its devices
  - RCC (Resource Constrained C/C++) platform support (e.g. software tool chains, etc.)

Contributions that don't involve code changes might be:
- Finding a new bug and reporting it
- Suggesting an enhancement to an existing feature, or a completely new feature
- Authoring a HOWTO describing a trick or technique you've figured out
- Correcting or proposing enhancements to documentation
- Writing an article advocating OpenCPI

## Contributing to Existing Projects
In order to facilitate awareness by the core development team and the
community, any bugs, enhancements, or features being worked on **MUST** have an
issue that describes _what_ you are working on.

Contributions to existing projects are usually:
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Submitting Bug Fixes](#submitting-bug-fixes)
- [Submitting Enhancements or New Features](#submitting-enhancements-or-new-features)

The last two will require a [merge request](#merge-requests).

### Reporting Bugs
Following these guidelines helps maintainers and the community understand your
report, reproduce the behavior, and find releated reports.

Before creating bug reports, please check this project's [issue list][issuelist]
as you might find that you don't need to create one. If you do find an issue
that **is still open**, add a comment to the existing issue instead of reporting
a new one. If you find an issue that **is closed**, create a new issue and
include a link to the closed issue in the description of your new one.

When you are creating a bug report, please include as many details as possible.
There are issue templates available for creating [new issues][newissue]. For a
bug report, the **Bug** template should be used as the information it asks for
helps OpenCPI Maintainers resolve issues faster.

**How to Submit a (Good) Bug Report**

If you are unable to use the template because you are reporting a bug using some
other means, the following should be provided as best as possible. Doing so will
help maintainers reproduce the problem:
- Describe the steps which reproduce the problem using as many details as
  possible. The more details the better. When listing steps, don't just say what
  you did, but explain how you did it. Provide the command(s), as typed, in the
  terminal.
- When giving terminal commands, use [Markdown code blocks](https://gitlab.com/help/user/markdown#code-spans-and-blocks)
  to format the commands so they are more readable.
- Describe the behavior you observed after following the steps and point out
  what the problem is with that behavior.
- Can you reliably reproduce this behavior? If not, provide details about how
  often the problem occurs and under which conditions it normally happens.
- Explain which behavior you expected to see instead and why.

Include details about your configuration and environment:
- Which version of OpenCPI are you using?
- Type of install (source or rpm)
- Environment variables (`env | grep -i ocpi | sort`)
- Operating system and version

### Suggesting Enhancements
Following these guidelines helps maintainers and the community understand your
suggestion and find releated suggestions.

Before creating enhancement suggestions, please check this project's
[issue list][issuelist] as you might find that you don't need to create one. If
you do find an issue that **is still open**, add a comment to the existing issue
instead of reporting a new one. If you find an issue that **is closed**, create
a new issue and include a link to the closed issue in the description of your
new one.

When you are creating an enhancement suggestion, please create a new
[new issue][newissue] and use the provided templates. For improving an existing
feature, the **Enhancement** template should be used. For suggesting a
completely new feature, the **Feature** template should be used. If you are
unsure, **Enhancement** can be used.

**How to Submit a (Good) Enhancement Suggestion**

If you are unable to use the templates because you are suggesting an enhancement
using some other means, the following should be provided as best as possible:
- Describe the existing feature/capability that you would like to have improved,
  and why. Be as detailed as possible and include step-by-step instructions.
- Any special hardware needed for the development and testing of this
  enhancement.
- What does the result look like so we know when it has been achieved?

### Submitting Bug Fixes
As a gentle reminder, when submitting a bug fix there should be an existing or
new issue related to the bug being fixed. See [Reporting Bugs](#reporting-bugs)
for more information about this process.

Depending on the severity and impact a bug has on users and the framework
respectively, it will either be accepted into a patch release or the next minor
release. Regardless, you should first begin by forking the repo and making
changes to a tagged release as a baseline. This ensures that the work is based
on a known good/stable code base.

If the changes are based on the current tagged release, are small and low-risk,
and of significant value, they _may_ be proposed as a "hot fix" to be put into a
patch release. In this case a [merge request](#merge-requests) may be submitted
for your branch that is based on the current tagged release.

If the changes are too complex, your merge request will likely be rejected with
the suggestion that the process in the
[Enhancements or New Features](#enhancements-or-new-features) section be
followed to get your changes into the next minor release. Basically, you will
need to merge your changes into the forked develop branch, retest, and then
create a new [merge request](#merge-requests) targeting the develop branch.

### Submitting Enhancements or New Features
As enhancements or new features generally involve a significant amount of work,
if you haven't already, you should review [Suggesting Enhancements](#suggesting-enhancements)
for our recommended way of proposing enhancements or new features.
Taking the time to submit a suggestion for an enhancement or new feature will
save time in the long run and will help provide the maintainers and community a
fourm in which to have discussions, help out, provide suggestions or lessons
learned, as well as receive updates about the enhancements or new features you
are interested in contributing.

Submitting enhancements or new features follow a slightly different process
from submitting bug fixes. You will still fork the repo, as this is the first
step for any contribution to an existing project, but instead of basing your
work on a tagged release, you will make your changes based off the develop
branch. Doing so will ensure any changes you make are done using the most
up-to-date version of the code base. This carries potential headaches because
the primary develop branch is not as stable, predictable, or documented as
release tags are. Nevertheless, your contribution is still greatly appreciated.

Once your changes have been made, and tested, you are ready to submit a merge
request. Once a [merge request](#merge-requests) has been submitted you will
get some level of feedback as to the viability of the code changes and possibly
some required changes before they are likely to be accepted. This feedback may
not be immediate, so be patient. The feedback may also suggest that the changes
be re-applied at a later date if the develop branch is in a state of flux in the
midst of a multi-stage set of changes, or if the request comes late in the
release cycle.

### Merge Requests
The process described here uses [GitLab Merge Requests](https://docs.gitlab.com/ee/user/project/merge_requests/) and has several goals:
- Maintain OpenCPI's quality
- Fix problems that are important to users
- Engage the community in working towards the best possible OpenCPI
- Enable a sustainable system for OpenCPI's maintainers to review
  contributions

Please follow these steps to have your contribution considered by the
maintainers:
- Follow all instructions in the merge request template
- When writing new code or modifying existing code, follow the [coding guidelines](https://gitlab.com/opencpi/opencpi/tree/develop/coding)
- After submitting your merge request, verify that your GitLab Pipeline passes
  - If your pipeline failes and you believe that the failure is unrelated to
    your change, please leave a comment on the merge request explaining why you
    believe the failure is unrelated. A maintainer will re-run the pipeline for
    you. If we conclude the failure is a false positive, then we will open an
    issue to track the problem and subsequently approve your merge request after
    further review of it.

While the prerequisites above **must** be satisified prior to having your merge
request reviewed, the reviewer(s) may ask you for additional information or
other changes before your merge request can be ultimately accepted.


## Contributing Projects
The previous section focused on contributions to the core repository, namely
[OpenCPI][opencpiurl], and it's built-in projects. This section focuses on
contributions that are **new** OpenCPI Projects.

>>>
The process for these types of contributions are still very much a work in
progress. Please bear with us as we continue to evolve these processes.
>>>

Contributed projects are mainly:
- [Applications and Components](#applications-and-components)
- [OpenCPI System Support Projects (OSP)](#opencpi-system-support-projects-osp)

### Applications and Components
This category of contributions is the least controlled, and is simply a way to
post a project to make it visible on the OpenCPI GitLab Site. Thus the
purpose of this repository is to make this type of contribution easily
accessible and visible under the OpenCPI GitLab Site without requiring many
separate repositories there. Actively developed and maintained projects would be
expected to have a home elsewhere, with this OpenCPI repository acting more like
a staging area for releases.

First, you need to download and install OpenCPI from [source][srcinstall].

Projects should be named according to the package-ID of the project.

After you are ready for your project to be contributed, you can create a
new issue requesting us to fork your project into OpenCPI's group on GitLab.

Projects contributed this way must contain a README file that:
- Makes it clear that while it is present in an OpenCPI GitLab repository, it
  has been submitted and maintained by a separate party.
- Includes a link or reference to your actual project.
- States which OpenCPI release the project is compatible and tested with.

Additional requests can be made to update your project(s) in this repository.
Requests should be made for each minor release of OpenCPI if your project is
actively maintained.

Tagging your code in a way that conveys which version of OpenCPI it is
compatible with is highly recommended. An example of such a tag is
`v1.0.0-opencpi-x.y.z` where **opencpi-x.y.z** is the version of OpenCPI your
project is compatible with.

It is also possible to have what amounts to an empty project which simply has a
README file that informs readers in the OpenCPI community about the project and
where it actually lives.

### OpenCPI System Support Projects (OSP)
If a new device is supported that will likely be used on multiple platforms and
cards, or a new card is supported that may be used on a variety of platforms,
it may be best to propose it as a change to the "assets" project in the core
OpenCPI repository. However, if the device support includes significant testing
assets (assemblies and/or applications, etc.), it may be better for it to be in
its own project. Making a reusable device its own project adds a burden to use
it, but if it takes a non-trivial project to provide such support, it is better
not to bloat the OpenCPI assets project with such significant contributions.

If an OSP is supporting a new system consisting of software (rcc) and
hardware (hdl) platforms, and devices specific to those platforms, then it is
best proposed as an OSP that will be placed within the
[OpenCPI System Support Projects (OSP) GitLab group][ospgroup].

Merge requests for projects to be updated in this repository should be made for
each minor release of OpenCPI if the project is actively maintained.

Tagging your code in a way that conveys which version of OpenCPI it is
compatible with is highly recommended. An example of such a tag is
`v1.0.0-opencpi-x.y.z` where **opencpi-x.y.z** is the version of OpenCPI your
project is compatible with.

Even when a contribution is submitted as its own project, parts of it may be
added to the OpenCPI core or assets project by OpenCPI maintainers if those
parts are considered broadly and likely reusable.

# Additional Resources

## Style Guides
[Git Commit Messages](https://gitlab.com/opencpi/opencpi/wikis/Gitlab-Branching-and-Workflow#commit-messages)  
[Coding](https://gitlab.com/opencpi/opencpi/tree/develop/coding)

## Versioning
OpenCPI uses [Semantic versioning](https://semver.org) and we highly encourage contributed projects to do the same.
