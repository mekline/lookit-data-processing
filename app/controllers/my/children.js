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
    profile: null,
    newProfile: function() {
        return this.get('store').createRecord('profile', {
            deleted: false
        });
    },

    onModelChange: Ember.observer('account', function() {
        this.set('profile', this.newProfile());
    }),
    actions: {
        profileAdded () {
            this.set('profile', this.newProfile());
            this.toggleProperty('addingNew');
        },
        toggleAddingNew () {
            this.toggleProperty('addingNew');
        },
        cancelAddProfile () {
            this.set('profile', this.newProfile());
            this.toggleProperty('addingNew');
        }
    }
});
