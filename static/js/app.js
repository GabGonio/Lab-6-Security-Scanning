// Warez Tracker frontend utilities
// Uses lodash for display formatting
var _ = require('lodash');

function formatRelease(release) {
  return _.template('<%= title %> [<%= platform %>]')(release);
}

function groupByCrew(releases) {
  return _.groupBy(releases, 'cracked_by');
}
