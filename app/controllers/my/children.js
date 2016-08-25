import Ember from 'ember';

const { service } = Ember.inject;

export default Ember.Controller.extend({
    session: service('session'),
    sessionAccount: service('session-account'),
    account: Ember.computed.alias('sessionAccount.account'),
    store: service(),
    toast: service(),

    addingNew: false,
    notAddingNew: Ember.computed.not('addingNew'),
    childProfile: null,
    newProfile: function() {
        this.set('childProfile', this.get('store').createRecord('profile', {
            deleted: false
        }));
    },
    init() {
	this.newProfile();
    },
    onModelChange: Ember.observer('account', function() {
        this.newProfile();
    }),
    actions: {
        profileAdded () {
	    this.newProfile();
            this.toggleProperty('addingNew');
        },
        toggleAddingNew () {
            this.toggleProperty('addingNew');
        },
        cancelAddProfile () {
	    this.newProfile();
            this.toggleProperty('addingNew');
        }
    }
});
