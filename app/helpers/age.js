import Ember from 'ember';
import moment from 'moment';

export function age([bd, ]) {
    let monthsOld = Math.floor(moment().diff(bd, 'months', true));
    if (monthsOld >= 12) {
        var yearsOld = Math.floor(monthsOld / 12);
        if (yearsOld > 1) {
            return `${yearsOld} years`;
        } else {
            return '1 year';
        }
    } else if (monthsOld >= 1) {
        if (monthsOld === 1) {
            return 'a month';
        } else {
            return `${monthsOld} months`;
        }
    } else {
        return 'less than a month';
    }
}

export default Ember.Helper.helper(age);
