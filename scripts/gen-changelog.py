#!/usr/bin/env python3
import argparse
import logging
import re
import sys
from datetime import datetime, timedelta

try:
    import gitlab
except ImportError as e:
    # To be replaced in 2.0 with proper Python dependencies
    # Recommended way to use pip within a program (but not best practice)
    # https://pip.pypa.io/en/latest/user_guide/#using-pip-from-your-program
    import os
    import subprocess

    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'python-gitlab'])
    os.execv(__file__, sys.argv)

PROJECT_ID = 12747880  # opencpi's project id


class ChangelogEntry(object):
    TYPE_MAP = {
        'bug': 'bug',
        'chore': 'chore',
        'doc': 'doc', 'docs': 'doc', 'documentation': 'doc',
        'enh': 'enh', 'enhancement': 'enh',
        'feat': 'feat', 'feature': 'feat',
    }
    CATEGORY_MAP = {
        'app': 'app', 'apps': 'app', 'application': 'app', 'applications': 'app',

        'comp': 'comp', 'comps': 'comp', 'component': 'comp', 'components': 'comp', 'worker': 'comp',

        'ci': 'devops', 'devop': 'devops', 'devops': 'devops',

        'hdl base': 'hdl base', 'hdl infrastructure': 'hdl base',

        'bsp': 'osp', 'bsps': 'osp', 'osp': 'osp', 'osps': 'osp',

        'framework': 'runtime', 'runtime': 'runtime',

        'test': 'tests', 'tests': 'tests',

        'build': 'tools', 'platform': 'tools', 'platforms': 'tools', 'prereq': 'tools', 'prereqs': 'tools',
        'tool': 'tools', 'tools': 'tools',
    }

    def __init__(self, issue_type: str, category: str, subject: str, mr_iid: int, sha: str):
        self.type = self.TYPE_MAP[issue_type.lower()]
        self.category = ''
        if len(category):
            self.category = ','.join(sorted([self.CATEGORY_MAP[x.strip()] for x in category.lower().split(',')]))
        self.subject = subject.strip()
        self.mr_iid = mr_iid
        self.sha = sha[:8]

    def __str__(self):
        return '{}: {}. (!{})({})'.format(self.category, self.subject.rstrip('.'), self.mr_iid, self.sha)

    def __lt__(self, other):
        return self.category < other.category

    def __eq__(self, other):
        return self.type == other.type and self.category == other.category and self.subject == other.subject

    def to_markdown(self):
        if len(self.category):
            return '- **{}**: {}. (!{})({})'.format(self.category, self.subject.rstrip('.'), self.mr_iid, self.sha)
        return '- {}. (!{})({})'.format(self.subject.rstrip('.'), self.mr_iid, self.sha)


class ChangelogSection(object):
    def __init__(self, name: str):
        self.name = name
        self.entries = []

    def __str__(self):
        s = ''
        if len(self.entries):
            s += '{}:\n'.format(self.name)
            s += '\n'.join(sorted(['  {}'.format(x) for x in self.entries]))
        return s

    def add_entry(self, entry: ChangelogEntry):

        self.entries.append(entry)

    def num_entries(self):
        return len(self.entries)

    def to_markdown(self):
        s = ''
        if len(self.entries):
            s += '### {}\n'.format(self.name)
            s += '\n'.join([x.to_markdown() for x in sorted(self.entries)])
        return s


class ChangelogRelease(object):
    SECTION_ORDER = ['feat', 'enh', 'bug', 'chore', 'doc']

    def __init__(self, release: str, previous_release: str, date=datetime.now()):
        self.date = date
        self.previous_release = previous_release
        self.release = release
        self.sections = {
            'bug': ChangelogSection(name='Bug Fixes'),
            'chore': ChangelogSection(name='Miscellaneous'),
            'doc': ChangelogSection(name='Documentation'),
            'enh': ChangelogSection(name='Enhancements'),
            'feat': ChangelogSection(name='New Features'),
        }

    def __str__(self):
        s = '{} ({})\n'.format(self.release, self.date.date())
        for section in self.SECTION_ORDER:
            if self.sections[section].num_entries():
                s += str(self.sections[section]) + '\n'
        return s[:-1]

    def add_entry(self, entry: ChangelogEntry):
        self.sections[entry.type].add_entry(entry)

    def num_entries(self):
        n = 0
        for section in self.sections:
            n += self.sections[section].num_entries()
        return n

    def to_markdown(self):
        s = '# [{current}](https://gitlab.com/opencpi/opencpi/compare/{previous}...{current}) ({date})\n\n'.format(
            current=self.release, previous=self.previous_release, date=self.date.date())
        for section in self.SECTION_ORDER:
            if self.sections[section].num_entries():
                s += self.sections[section].to_markdown() + '\n\n'
        return s[:-2]


def main():
    logging.info('Connecting to GitLab')
    gl = gitlab.Gitlab('https://gitlab.com', private_token=args.gitlab_token)
    gl.auth()
    logging.info('Getting project info from GitLab')
    project = gl.projects.get(PROJECT_ID, lazy=True)

    # Determine start time based on previous release
    try:
        logging.info('Verifying previous release {}'.format(args.previous_release))
        tag = project.tags.get('{}'.format(args.previous_release))
        created_at = tag.commit['created_at']
        start = datetime.strptime(created_at[:created_at.index('.')], '%Y-%m-%dT%H:%M:%S')
        start -= timedelta(seconds=5)  # subtract a couple seconds due to how tags are created on gitlab
        logging.info('Found previous release {} released on {}'.format(args.previous_release, start))
    except gitlab.GitlabGetError as err:
        logging.critical('Could not find {}: {}'.format(args.previous_release, err))
        return 1

    # Determine end time based on release specified, if it exists
    try:
        logging.info('Looking for release {}'.format(args.release))
        tag = project.tags.get('{}'.format(args.release))
        created_at = tag.commit['created_at']
        end = datetime.strptime(created_at[:created_at.index('.')], '%Y-%m-%dT%H:%M:%S')
        end += timedelta(seconds=5)  # add a couple seconds due to how tags are created on gitlab
        logging.info('Found release {} released on {}'.format(args.release, end))
    except gitlab.GitlabGetError as err:
        end = datetime.now()

    # Get x.y.z part of vx.y.z-rc.1
    ocpi_version = re.match(r'v([0-9]+\.[0-9]+\.[0-9]+)', args.release).group(1)
    target_release = 'target release::{}'.format(ocpi_version)

    # Process each MR in the time frame, checking for changelog entries
    changelog_release = ChangelogRelease(release=args.release, previous_release=args.previous_release, date=end)
    logging.info('Processing merged Merge Requests for "{}"'.format(target_release))
    for mr in project.mergerequests.list(as_list=False, state='merged', order_by='created_at', sort='asc',
                                         target_branch='master', labels=[target_release]):
        merged_at = datetime.strptime(mr.merged_at[:mr.merged_at.index('.')], '%Y-%m-%dT%H:%M:%S')
        workflow = [label for label in mr.labels if label.startswith('workflow::')][0]
        logging.debug('{} {} {} {} {}'.format(mr.merged_at, workflow, mr.title, mr.iid, mr.sha))

        # In time frame?
        if not start < merged_at <= end:
            logging.debug('OLD: start={} merged_at={} end={}'.format(start, merged_at, end))
            continue

        # Look for changelog entry
        for line in mr.description.split('\n'):
            match = re.match(r'(?:- )?([a-z]+)\(([a-z, ]*)\):\s*(.*)$', line, re.IGNORECASE)
            if match is None:
                continue
            logging.debug('FOUND CHANGELOG ENTRY: {}'.format(match.groups()))
            changelog_entry = ChangelogEntry(issue_type=match.group(1), category=match.group(2),
                                             subject=match.group(3), mr_iid=mr.iid, sha=mr.sha)
            changelog_release.add_entry(changelog_entry)

    logging.info('Found {} new changelog entries.'.format(changelog_release.num_entries()))
    print(changelog_release.to_markdown())
    return 0


# Setup argparse
parser = argparse.ArgumentParser(
    description='Generates a CHANGELOG.md file for OpenCPI based on the release and previous release given.'
)
parser.add_argument('gitlab_token', help='A GitLab API Token that gives you read access to the GitLab Project that '
                                         'a changelog will be generated for')
parser.add_argument('release', help='The name of the release (ex. v1.6.0)')
parser.add_argument('previous_release', help='The name of previous release (ex. v1.5.0)')
parser.add_argument('--workflow', choices=['merged', 'staged', 'released'], help='Workflow state to filter on')
parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')

# Parse args
args = parser.parse_args()

# Setup logger
logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', level=logging.INFO)
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

# Validate release arguments
for r in [args.release, args.previous_release]:
    if re.match(r'v[0-9]+\.[0-9]+\.[0-9]+', r) is None:
        logging.critical('{} is not a valid release, must be of the form "v1.2.3".')
        exit(1)
if args.release == args.previous_release:
    logging.critical('Release and Previous Release are the same: {}'.format(args.release))
    exit(1)

exit(main())
