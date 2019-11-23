This issue template is for adding an external project, granting that project
access to OpenCPI's distributed test lab infrastructure. This will allow you
to test your application or component on actual hardware and simulators that
you currently don't own.

**NOTE:** Only projects hosted on gitlab.com are supported.

### Why you want to add an external project
(Describe what your project does.)


### Your project's runner registration token
Your runner's registration token is located at
https://gitlab.com/**namespace**/**project_name**/-/settings/ci_cd

The easiest way to find this is to:
- Go to your project's GitLab page
- Click **Settings**
- Click **CI / CD**
- In the Runners section, click **Expand**
- Scroll down until you see **Set up a specific Runner manually**
- The third step will contain your project's runner registration token

**NOTE:** This issue will be marked confidential by default so this runner's
token is not available to the general public.


/label ~"type::chore"
/confidential
