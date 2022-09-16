function delete_qualification(qual_id, where) {
    console.log('Going to delete qualification  ' + qual_id + ' where:' + where)
    $.ajax({
      url: `/mturk/${where}/qualification/${qual_id}`,
      type: 'DELETE',
      success: function(result) {
          console.log('Delete Success')
          console.log(result)
          $('#'+qual_id).hide()
      },
      error: function(result) {
        alert("Error while deleting the qualification: " + qual_id )
        console.log('Error while deleting qualification')
        console.log(result)
      },
  });
}

function delete_hit(hit_id, where) {
    console.log('Going to delete HIT ' + hit_id + ' where :' + where)
    $.ajax({
      url: `/mturk/${where}/HIT/${hit_id}`,
      type: 'DELETE',
      success: function (result) {
        console.log('Delete Success')
        console.log(result)
        $('#' + hit_id).hide()
      },
      error: function (result) {
        alert("Error while deleting the hit: " + hit_id)
        console.log('Error while deleting HIT')
        console.log(result)
      },
    });
  }

function disqualify(worker_id, qual_id, where){
  console.log(`Going to disqualify ${worker_id} from ${qual_id} ; where: ${where}`)
  $.ajax({
    url: `/mturk/${where}/worker/${worker_id}/qualification/${qual_id}`,
    type: 'DELETE',
    success: function (result) {
      console.log(`Worker ${worker_id} removed from qualification ${qual_id}`)
      console.log(result)
      $('#' + worker_id).hide()
    },
    error: function (result) {
      alert(`Error while disassociating qualification. Check logs`)
      console.log('Error while revoking qualification')
      console.log(result)
    },
  });
}
