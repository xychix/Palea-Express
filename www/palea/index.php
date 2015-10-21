<?php

$session = $_REQUEST['se'];

if ( $db = new PDO("sqlite:../../var/palea.db")){

	printf("<html><head>");
	printf("  <link href=\"style.css\" rel=\"stylesheet\" type=\"text/css\">");
	printf("  <title>Choose your session see results</title>");
	printf("  <meta http-equiv=\"refresh\" content=\"5\"/>");
	printf("</head>");
	printf("<body><table width=100%%><tr><td class=\"invisible\"><h1>Choose your session to see results</h1></td>");
	printf("<td class=\"invisible\" align=\"right\"><img src=\"logo.jpg\"></td></tr></table>");


// End of header, the value tables start here
	//$resultset = $db->query("SELECT timestamp, session, count(*) as count FROM catch GROUP BY session ORDER BY timestamp DESC;");
	$resultset = $db->query("SELECT timestamp, session, count(*) as count FROM catch WHERE gateway NOT LIKE \"127.0.0.1\" AND gateway NOT LIKE \"77.235.37.117\" GROUP BY session ORDER BY timestamp DESC;");
	printf("<table><tr><td class=\"invisible\" colspan=\"3\"><h2>Sessions and # of results</h2></td></tr>");
	printf("<tr><td class=\"head\">Last received packet on:</td><td class=\"head\">Remarks</td><td class=\"head\">Session</td>");
	printf("<td class=\"head\"># received packages</td><td class=\"head\">ACTION</td></tr>");
	$cnt = 1;
	while($result = $resultset->fetch()){
		$remark = "&nbsp;";
		if( ($result['session']  == 0) && ($result['timestamp'] > (time() -120) ) ){
			$remark = "<b><font color=\"00DD00\">Hartbeat! system alive!</font></b>";
		}elseif(  ($result['session']  == 0) ){
			$delay = time()-$result['timestamp'];
			settype($delay,"int");
			$remark = "<b><font color=\"FF0000\">ALARM no hartbeat recieved for " . $delay .  " seconds!</font>";
		}elseif( $result['timestamp'] > (time()-60) ){
			$remark = "<b><font color=\"FF0000\">Scan still running!</font></b>";
		}elseif( $result['timestamp'] < (time()-43200) ){
			 $remark = "<b><font color=\"CCCCCC\">Scan is older than 5 days!</font></b>";
		}

		printf("<tr><td> %s </td>",  strftime("%Y-%m-%d %H:%M:%S" ,$result['timestamp']) );
		printf("<td> %s </td>", $remark );
		printf("<td><a href=\"report.php?se=%s\">%s</a></td>", $result['session'], $result['session'] );
		printf("<td> %s </td>", $result['count'] );
		printf("<td>");
		printf("<a href=\"delete.php?se=%s\"><img src=delete.png border=0 width=16 alt=\"Delete\"></a>&nbsp", $result['session'] );
		printf("<a href=\"report.php?se=%s\"><img src=report.png border=0 width=16 alt=\"Report\"></a>&nbsp", $result['session'] );
		printf("</td></tr>");
	}
	printf("</table></body></html>");

}
?>
