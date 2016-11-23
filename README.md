# Lookit

This README outlines the details of collaborating on this Ember application.
A short introduction of this app could easily go here.

## Prerequisites

You will need the following things properly installed on your computer.

* [Git](http://git-scm.com/)
* [Node.js](http://nodejs.org/) (with NPM)
* [Bower](http://bower.io/)
* [Ember CLI](http://www.ember-cli.com/)
* [PhantomJS](http://phantomjs.org/)

## Installation

```bash
git clone https://github.com/CenterForOpenScience/lookit.git
cd lookit
npm install
bower install
git submodule init
git submodule update

cd lib/exp-player
npm install
bower install

cd ../exp-models
npm install
bower install
```

To use the video capture facilities of Lookit, you will also need to place the file `VideoRecorder.swf` 
in your `lookit/public/` folder. **This file is not part of the git repository**; it is from the HDFVR flash video 
recorder and must be obtained from a team member with access to the licensed version.

## Running / Development

#### Configuration

1. Create a staging-OSF developer application [here](https://staging.osf.io/settings/applications/)
2. Create or open a file named '.env' in the root of the lookit directory, and add the following entries:
```bash
OSF_CLIENT_ID=<application_client_id>
OSF_SCOPE=osf.users.all_read
OSF_URL=https://staging-accounts.osf.io

WOWZA_PHP='{"minRecordTime":1,"showMenu":"false","showTimer":"false","enableBlinkingRec":1,"skipInitialScreen":1,"recordAgain":"false","showSoundBar":"true","hideDeviceSettingsButtons":1,"microphoneGain": 60,"connectionstring":"CONNECTIONSTRING"}'
WOWZA_ASP='{"showMenu":"false","loopbackMic":"true","skipInitialScreen":1,"showSoundBar":"true","snapshotEnable":"false"}'

JAMDB_URL=https://staging-metadata.osf.io
JAMDB_NAMESPACE=experimenter

SENTRY_DSN=""
```

A more complete configuration string is available upon request. In this application, we typically use `WOWZA_PHP` 
for settings in which a video is actually recorded, and `WOWZA_ASP` for video preview screens where no video is to be saved.
The value of `connectionstring` is available internally but not committed to Github; **it must be replaced 
with a reference to the streaming server.**  Other settings are as described in the sample `avc_settings.php` file 
provided in the HDFVR installation zip file.

3. Run the server with:
```bash
ember server --environment staging
```

which will point your local copy of the Lookit site pointed at the staging database.

####  Modifying static content

To get an overview of the URL structure of the Lookit site, it's best to look at the file `app/router.js`. Notice some entries like:

```javascript
    this.route('faq');
    this.route('scientists');
    this.route('resources');
    this.route('contact');
```

Ember.js enforces a very strict convention over configuration model. This means the names user here must correspond directly with files in `app/templates/`, `app/routes/`, and `app/controllers`.
For example, the 'faq' route has a corresponding template file  `app/templates/faq.hbs`. Templates are compiled using [handlebars.js](http://handlebarsjs.com/), hence the .hbs extention. Generally
for modifying most static content it's sufficient to modify the template for the page that needs changing.

##### Sub-routes

The [Ember Guides](https://guides.emberjs.com/v2.3.0/routing/defining-your-routes/) have the best description of sub-routes and template organization under those routes.

##### Components

Some pages utilize Ember components (self-contained pairs of JS code and a template file). Some of these components are third party, but others are part of the Lookit codebase. To explore this more,
take the example of the `resources` page:
```html
...
        <div class="resources-item">
            <h3>Find a developmental lab near you</h3>
            <p>
                Interested in participating in research in person?
                Find a list of labs that study child development in your state.
            </p>
            <p>
                Did we miss your lab, or one you know about? Our apologies, and please let us kow at
                <a href="mailto:lookit-ed@mit.edu">lookit-ed@mit.edu</a>
            </p>
            {{find-local-lab}}
        </div>
...
```

Notice the special `{{find-local-lab}}` syntax. This is Ember's cue to lookup the find-local-lab component and render it at this point in the HTML document. Components tend to be organized two ways:

1. Separate JS and .hbs:
   - `app/components/<component-name>.js`
   - `app/templates/components/<component_name>.hbs`
2. 'Pod' structure:
   - `app/components/<component_name>/component.js`
   - `app/components/<component_name>/template.hbs`

So to change the look and feel of the find-local-tab component, just find and modify its template file.


