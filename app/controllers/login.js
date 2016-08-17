import Ember from 'ember';

import config from 'ember-get-config';

export default Ember.Controller.extend({
    modal: false,
    queryParams: ['ref'],
    session: Ember.inject.service('session'),

    isIE: /(MSIE|rv:11.0)/i.test(navigator.userAgent),

    invalidAuth: false,
    userConflict: false,
    creatingUser: false,

    resetId: null,
    resetSent: false,
    actions: {
        authenticate(attrs) {
            this.get('session')
                .authenticate('authenticator:jam-jwt', attrs)
                .then(() => this.get('ref') ? this.transitionToRoute(...this.get('ref').split(':')) : null)
                .catch(() => this.send('toggleInvalidAuth'));
        },
        toggleInvalidAuth() {
            this.toggleProperty('invalidAuth');
        },
        createAccount(attrs) {
            this.set('creatingUser', true);
            var newAccount = this.store.createRecord('account', {
                username: attrs.username,
                password: attrs.password,
                email: attrs.email,
                profiles: [],
                emailPreferencesNextSession: true,
                emailPreferencesNewStudies: true,
                emailPreferencesResultsPublished: true,
                // Update the line below to be more general
                id: `${attrs.username}`
            });
            newAccount.save().then(() => {
                // log in immediately with this new account information
                var theAttrs = {provider: 'self', namespace: config.JAMDB.namespace, collection: 'accounts', username: attrs.username, password: attrs.password};
                this.send('authenticate', theAttrs);
            }, (res) => {
                this.set('creatingUser', false);
                if(res.errors[0].status === '409') {
                    this.send('toggleUserConflict');
                }
                else {
                    this.send('toggleInvalidAuth');
                }
            });
        },
	resetPassword() {
	    let options = Ember.getOwner(this).lookup('adapter:application').ajaxOptions();
	    Ember.$.ajaxSetup(options);
	    let url = `${config.JAMDB.url}/v1/id/collections/${config.JAMDB.namespace}.accounts/user`;
	    Ember.$.ajax({
		url: url,
		method: 'POST',
		data: JSON.stringify({
		    data: {
			type: "reset",
			attributes: {
			    id: this.get('resetId')
			}
		    }
		})
	    }).then(() => this.set('resetSent', true));
	},
        toggleUserConflict() {
            this.toggleProperty('userConflict');
        },
        toggleCreatingUser() {
            this.toggleProperty('creatingUser');
        }
    }
});
