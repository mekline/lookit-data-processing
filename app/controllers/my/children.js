import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service(),

    store: Ember.inject.service(),
    toast: Ember.inject.service(),

    addingNew: false,
    notAddingNew: Ember.computed.not('addingNew'),
    childProfile: null,
    newProfile: function () {
        this.set('childProfile', this.get('store').createRecord('profile', {
            deleted: false
        }));
    },
    init() {
        this.newProfile();
    },
    onModelChange: Ember.observer('model', function () {
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
