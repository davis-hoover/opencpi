# Contributing to OpenCPI
Contributing to the OpenCPI community of developers and users is a wonderful
thing!

It helps improve the framework, adds support for new devices and platforms, and
components and applications for others to use, build on, and understand -- all
of which makes OpenCPI more attractive, expands the community, and makes it more
valuable to users. The framework maintainers will make every feasible effort to
incorporate all contributions, subject to the suitability of the contributions
and the time available to review and accept them.

While many developers work on fixing bugs and creating new features, there is
a wide array of items non-programmers can help impove upon. If you're here,
you probably already have an idea of something you'd like to work on.

If not, here are just a few ways you can help:
- Pick a bug, fix it, and send in a merge request on GitLab.
- Choose a feature you want to see developed, and make it or a ticket for it.
- Find a new bug and report it.
- Create a new application, component or board support package and share it.
- Write an article advocating OpenCPI.
- Author a HOWTO describing a trick or technique you've figured out.

Before investing significant time on a contribution, especially in the core of
OpenCPI itself, it is a good idea to find out if anyone is already working on
the same thing by using the
[issues list](https://gitlab.com/groups/opencpi/-/issues) on GitLab. Another
source of information is the email discussion list at
discuss@lists.opencpi.org. To post on this list you must subscribe to it at
http://lists.opencpi.org.

**All contributions become part of OpenCPI, subject to the LGPL3 license,
unless other arrangements are specifically made (which is rare).**

## Ways to Contribute

In the rest of this document, the term _project_ is used to mean OpenCPI
projects, and not the way GitLab uses the term.
Additionally, submitting/proposing/contributing to OpenCPI will require some
familiarity with the _git_ SCM tool and the gitlab.com site. The text that
follows assumes this.

Contributions to OpenCPI generally fall into three categories:
1. Contributed projects consisting of:
   - Useful/reusable components, workers and tests
   - Useful applications, either simply for reference or as interesting
     baselines or examples
2. Contributed projects that act as Board Support Packages (BSP) consisting of:
   - HDL devices, cards, and platforms
   - HDL assemblies and applications for testing/exercising the platform and/or
     its devices
   - RCC platform support (e.g. software tool chains, etc.)
3. Changes to the core repository of opencpi consisting of:
   - Bug fixes and enhancements to the framework software
   - Bug fixes and enhancements to the included projects (core and assets)


### 1. Contributed Projects Containing Useful Components and Applications

This category of contributions is the least controlled, and is simply a way to
post a project to make it visible on the OpenCPI GitLab group site. Thus the
purpose of this repository is to make this type of contribution easily
accessible and visible under the OpenCPI GitLab account without requiring many
separate repositories there. Actively developed and maintained projects would be
expected to have a home elsewhere, with this OpenCPI repository acting more like
a staging area for releases.

First, you need to download and install OpenCPI from source or RPMs.
More info on this process is found
[here](http://opencpi.github.io/OpenCPI_Installation.pdf).

Projects should be named according to the package-ID of the project.

After you are ready for your project to be contributed back, you can create a
new issue requesting us to fork your project into OpenCPI's group on GitLab.

Projects contributed this way must contain a README file that:
- Makes it clear that while it is present in an OpenCPI GitLab repository, it
  has been submitted and maintained by a separate party.
- Includes a link or reference to your actual project on GitLab.
- States which OpenCPI release the project is compatible and tested with.

Additional requests can be made to update your project(s) in this repository.
Requests should be made for each minor release of OpenCPI if your project is
actively maintained.

Tagging your code in a way that conveys which version of OpenCPI it is
compatible with is highly recommended. An example of such a tag is
`v1.0.0-opencpi-1.6.0` where **opencpi-1.6.0** is the version of OpenCPI your
project is compatible with. There should be only one tag per compatible version.
Multiple tags can be created for each compatible version.

It is also possible to have what amounts to an empty project which simply has a
README file that informs readers in the OpenCPI community about the project and
where it actually lives.


### 2. BSP Projects for Supporting New Devices and Platforms

If a new device is supported that will likely be used on multiple platforms and
cards, or a new card is supported that may be used on a variety of platforms,
it may be best to propose it as a change to the "assets" project in the core
OpenCPI repository. However, if the device support includes significant testing
assets (assemblies and/or applications, etc.), it may be better for it to be in
its own project. Making a reusable device its own project adds a burden to use
it, but if it takes a non-trivial project to provide such support, it is better
not to bloat the OpenCPI assets project with such significant contributions.

If a BSP project is supporting a new system consisting of software (rcc) and
hardware (hdl) platforms, and devices specific to those platforms, then it is
best proposed as a BSP project that will be placed within the [OpenCPI System
Support Projects (OSP) GitLab group](https://gitlab.com/opencpi/osp).

Merge requests for projects to be updated in this repository should be made for
each minor release of OpenCPI if the project is actively maintained. No merge
request should touch more than one project.

Tagging your code in a way that conveys which version of OpenCPI it is
compatible with is highly recommended. An example of such a tag is
`v1.0.0-opencpi-1.6.0` where **opencpi-1.6.0** is the version of OpenCPI your
project is compatible with. There should be only one tag per compatible version.
Multiple tags can be created for each compatible version.

Even when a contribution is submitted as its own project, parts of it may be
added to the OpenCPI core or assets project by OpenCPI maintainers if those
parts are considered broadly and likely reusable.


### 3. Changes to the Core Repository

Changes are proposed using the standard forking and merge request process
described in: https://docs.gitlab.com/ee/workflow/forking_workflow.html.
However, it is recommended that changes to the core repository be done in two
steps.

The first step makes changes using a GitLab tagged release as a baseline.
I.e. the work should be done on a branch originating from the current/latest
release tag. This ensures that the work is based on a known good/stable code
base, and it allows the work to be easily tested and then shared with others
using a patch file based on that release tag that can be used against the core
repository.

If the changes are based on the current tagged release, and they are small and
low-risk, and of significant value, they *may* be proposed as a "hot fix" to be
put into a patch release (e.g. 1.5.x where "x" is the patch release number).
In this case, a merge request may be submitted for your branch that is based on
the latest release tag. If the changes are at all complex or not of high value,
the merge request will likely be rejected, with the suggestion that the
next/second step below be taken to put the changes into the next minor release
(e.g. 1.x.0 where "x" is the minor release).

The second step is to prepare and test the changes in a way that can be
efficiently adopted/accepted into the develop branch in order for it to be
included in the next (minor) release. This step carries potential headaches
because the primary develop branch is not as stable or predictable or documented
as release-tags. But this process is to make a branch off the develop branch,
re-apply and merge the changes from the first step, retest, and then create a
merge request for this second branch.

At this time you will get some level of feedback as to the viability of the code
changes and possibly some required changes before they are likely to be
accepted. This feedback may not be immediate, so be patient. The feedback may
also suggest that the changes be re-applied at a later date if the develop
branch is in a state of flux in the midst of a multi-stage set of changes.


## Git Practices
Our Git branching strategy is located in the wiki [here](https://gitlab.com/opencpi/opencpi/wikis/Gitlab-Branching-and-Workflow)


## Coding Style
See documents located [here](https://gitlab.com/opencpi/opencpi/tree/develop/coding)


## Versioning
OpenCPI uses [Semantic versioning](https://semver.org/)