/* jshint node: true */

module.exports = function(environment) {
    var ENV = {
        modulePrefix: 'lookit-base',
        environment: environment,
        baseURL: '/',
        locationType: 'auto',
        EmberENV: {
            FEATURES: {
                // Here you can enable experimental features on an ember canary build
                // e.g. 'with-controller': true
            }
        },
        'ember-simple-auth': {
            authenticationRoute: 'login',
            routeAfterAuthentication: 'home',
            routeIfAlreadyAuthenticated: 'home'
        },
        APP: {
            // Here you can pass flags/options to your application instance
            // when it is created
        }
    };

    if (environment === 'development') {
        // ENV.APP.LOG_RESOLVER = true;
        // ENV.APP.LOG_ACTIVE_GENERATION = true;
        // ENV.APP.LOG_TRANSITIONS = true;
        // ENV.APP.LOG_TRANSITIONS_INTERNAL = true;
        // ENV.APP.LOG_VIEW_LOOKUPS = true;
    }

    if (environment === 'staging' || environment === 'production') {
        ENV.JAMDB = {
            authorizer: 'jam-jwt',
            collection:'accounts',
            url: process.env.JAMDB_URL,
            namespace: process.env.JAMDB_NAMESPACE
        };
    }

    if (environment === 'staging') {
        ENV.ASM_MAPPING = {
            nextSession: {
                label: 'Next Session',
                description: 'It\'s time for another session of a study we are currently participating in',
                id: '911'
            },
            newStudies: {
                label: 'New Studies',
                description: 'A new study is available for one of my children',
                id: '913'
            },
            resultsPublished: {
                label: 'Results Published',
                description: 'The results of a study we participated in are published',
                id: '915'
            },
            optOut: {
                label: 'Opt Out',
                description: 'A researcher may also email you personally if we have questions about your responses (for example, if you report two different birthdates for a child and we\'re not sure whether he\'s 3 or 5) or if you report a technical problem. Check here to opt out:',
                id: '1117'
            }
        };
    }
    
    if (environment === 'production') {
        ENV.ASM_MAPPING = {
            nextSession: {
                label: 'Next Session',
                description: 'It\'s time for another session of a study we are currently participating in',
                id: '915'
            },
            newStudies: {
                label: 'New Studies',
                description: 'A new study is available for one of my children',
                id: '917'
            },
            resultsPublished: {
                label: 'Results Published',
                description: 'The results of a study we participated in are published',
                id: '919'
            },
            optOut: {
                label: 'Opt Out',
                description: 'A researcher may also email you personally if we have questions about your responses (for example, if you report two different birthdates for a child and we\'re not sure whether he\'s 3 or 5) or if you report a technical problem. Check here to opt out:',
                id: '921'
            }
        };
    }

    if (environment === 'test') {
        // Testem prefers this...
        ENV.baseURL = '/';
        ENV.locationType = 'none';

        // keep test console output quieter
        ENV.APP.LOG_ACTIVE_GENERATION = false;
        ENV.APP.LOG_VIEW_LOOKUPS = false;

        ENV.APP.rootElement = '#ember-testing';
    }

    return ENV;
};
