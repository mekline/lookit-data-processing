import Ember from 'ember';


export default Ember.Component.extend({
    session: null,

    showFeedback: false,
    feedbackText: 'Show Feedback',

    store: Ember.inject.service(),

    profileName: null,

    init() {
	this._super(...arguments);
	this.get('session').getProfile().then((profile) => {
	    this.set('profileName', profile.get('firstName'));
	});
    },

    arguments: {
        toggleFeedback: function() {
            this.toggleProperty('showFeedback');
            if (this.get('showFeedback')) {
                this.set('feedbackText', 'Hide Feedback');
                var session = this.get('session');
                session.set('hasReadFeedback', true);
                session.save().then(this.set('session', session));
            } else {
                this.set('feedbackText', 'Show Feedback');
            }

        }
    }
});
